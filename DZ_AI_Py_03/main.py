import os
import sys
import wave
from datetime import datetime

import numpy as np
from PIL import Image, UnidentifiedImageError
from transformers import pipeline, BlipProcessor, BlipForConditionalGeneration

CAPTION_MODEL = "Salesforce/blip-image-captioning-base"

TTS_MODELS = {
    "1": ("facebook/mms-tts-eng", "швидка, легка модель"),
    "2": ("suno/bark-small", "природніше звучання, повільніша і важча модель"),
}
DEFAULT_TTS_KEY = "1"

INPUT_DIR = "input"
OUTPUT_DIR = "output"
DESCRIPTIONS_FILE = os.path.join(OUTPUT_DIR, "descriptions.txt")
ALLOWED_EXT = {".jpg", ".jpeg", ".png"}


def ensure_dirs():
    os.makedirs(INPUT_DIR, exist_ok=True)
    os.makedirs(OUTPUT_DIR, exist_ok=True)


def load_caption_model():
    print(f"Завантаження моделі опису: {CAPTION_MODEL}")
    processor = BlipProcessor.from_pretrained(CAPTION_MODEL)
    caption_model = BlipForConditionalGeneration.from_pretrained(CAPTION_MODEL)
    return processor, caption_model


def make_tts(name: str) -> dict:
    print(f"Завантаження TTS-моделі: {name}")
    return {"name": name, "pipe": pipeline("text-to-speech", model=name)}


def choose_tts_key() -> str:
    print("\nДоступні TTS-моделі:")
    for key, (name, desc) in TTS_MODELS.items():
        print(f"  {key} - {name} ({desc})")
    while True:
        choice = input(f"Оберіть TTS-модель (Enter - {DEFAULT_TTS_KEY}): ").strip() or DEFAULT_TTS_KEY
        if choice in TTS_MODELS:
            return choice
        print("Невірний вибір, введіть номер із списку.")


def validate_image(path: str):
    if not path:
        return "Шлях не може бути порожнім."
    if not os.path.isfile(path):
        return f"Файл не знайдено: {path}"
    ext = os.path.splitext(path)[1].lower()
    if ext not in ALLOWED_EXT:
        return f"Непідтримуваний формат {ext}. Дозволені: JPG, JPEG, PNG."
    try:
        with Image.open(path) as img:
            img.verify()
    except (UnidentifiedImageError, OSError) as e:
        return f"Не вдалося відкрити зображення: {e}"
    return None


def describe_image(captioner, path: str) -> str:
    processor, model = captioner
    image = Image.open(path).convert("RGB")
    inputs = processor(images=image, return_tensors="pt")
    output_ids = model.generate(**inputs, max_new_tokens=50)
    text = processor.decode(output_ids[0], skip_special_tokens=True).strip()
    if not text:
        raise RuntimeError("Модель не змогла створити опис зображення.")
    return text[0].upper() + text[1:]


def synthesize_speech(tts: dict, text: str, out_path: str) -> str:
    out = tts["pipe"](text)
    audio = np.asarray(out["audio"], dtype=np.float32).squeeze()
    rate = int(out["sampling_rate"])
    if audio.size == 0:
        raise RuntimeError("TTS-модель повернула порожнє аудіо.")
    pcm = (np.clip(audio, -1.0, 1.0) * 32767).astype(np.int16)
    with wave.open(out_path, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(rate)
        wf.writeframes(pcm.tobytes())
    return out_path


def ask_audio_name(default: str) -> str:
    name = input(f"Назва аудіофайлу (Enter - {default}): ").strip()
    name = os.path.basename(name) or default
    if not name.lower().endswith(".wav"):
        name += ".wav"
    return os.path.join(OUTPUT_DIR, name)


def save_description(image_name: str, description: str, audio_path: str, tts_name: str) -> None:
    stamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        with open(DESCRIPTIONS_FILE, "a", encoding="utf-8") as f:
            f.write(f"[{stamp}] {image_name}\n")
            f.write(f"Опис: {description}\n")
            f.write(f"TTS-модель: {tts_name}\n")
            f.write(f"Аудіо: {audio_path}\n\n")
    except OSError as e:
        print(f"Не вдалося зберегти descriptions.txt: {e}")


def print_summary(result: dict) -> None:
    print("\n=== Результат ===")
    print(f"Фотографія:      {result['image']}")
    print(f"Опис:            {result['description']}")
    print(f"Модель опису:    {CAPTION_MODEL}")
    print(f"TTS-модель:      {result['tts_model']}")
    print(f"Аудіофайл:       {result['audio']}")


def process_image(captioner, tts: dict, path: str, ask_name: bool = False):
    error = validate_image(path)
    if error:
        print(f"Помилка: {error}")
        return None

    image_name = os.path.basename(path)
    print("Аналіз зображення...")
    try:
        description = describe_image(captioner, path)
    except Exception as e:
        print(f"Помилка аналізу: {e}")
        return None
    print(f"Опис зображення: {description}")

    default_name = os.path.splitext(image_name)[0] + "_description"
    out_path = ask_audio_name(default_name) if ask_name else os.path.join(
        OUTPUT_DIR, default_name + ".wav")

    print("Генерація мовлення...")
    try:
        audio_path = synthesize_speech(tts, description, out_path)
    except Exception as e:
        print(f"Помилка синтезу мовлення: {e}")
        return None

    save_description(image_name, description, audio_path, tts["name"])
    result = {"image": image_name, "description": description,
              "audio": audio_path, "tts_model": tts["name"]}
    print(f"Аудіо збережено: {audio_path}")
    print_summary(result)
    return result


def mode_batch(captioner, tts: dict):
    files = sorted(f for f in os.listdir(INPUT_DIR)
                   if os.path.splitext(f)[1].lower() in ALLOWED_EXT)
    if not files:
        print(f"У папці {INPUT_DIR}/ немає фотографій (JPG, JPEG, PNG).")
        return None
    print(f"Знайдено фотографій: {len(files)}")
    last = None
    for i, f in enumerate(files, 1):
        print(f"\n--- {i}/{len(files)}: {f} ---")
        result = process_image(captioner, tts, os.path.join(INPUT_DIR, f))
        last = result or last
    return last


def mode_revoice(tts: dict, last):
    if last is None:
        print("Спочатку проаналізуйте хоча б одну фотографію.")
        return
    out_path = ask_audio_name(os.path.splitext(last["image"])[0] + "_repeat")
    try:
        synthesize_speech(tts, last["description"], out_path)
        print(f"Повторне аудіо збережено: {out_path} (TTS-модель: {tts['name']})")
    except Exception as e:
        print(f"Помилка синтезу мовлення: {e}")


MENU = """
=== AI Vision & Voice Assistant ===
1 - Аналіз фотографії (вказати шлях)
2 - Пакетна обробка папки input/
3 - Повторно озвучити останній опис
4 - Змінити TTS-модель
0 - Вихід
"""


def main():
    ensure_dirs()
    try:
        captioner = load_caption_model()
        tts = make_tts(TTS_MODELS[choose_tts_key()][0])
    except Exception as e:
        print(f"Помилка завантаження моделей: {e}")
        print("Перевірте інтернет і встановлення: pip install transformers torch pillow numpy")
        sys.exit(1)

    last = None
    while True:
        print(MENU)
        print(f"Поточна TTS-модель: {tts['name']}")
        choice = input("Ваш вибір: ").strip()
        try:
            if choice == "1":
                path = input("Шлях до фото: ").strip()
                last = process_image(captioner, tts, path, ask_name=True) or last
            elif choice == "2":
                last = mode_batch(captioner, tts) or last
            elif choice == "3":
                mode_revoice(tts, last)
            elif choice == "4":
                new_name = TTS_MODELS[choose_tts_key()][0]
                if new_name != tts["name"]:
                    tts = make_tts(new_name)
                    print(f"TTS-модель змінено на: {new_name}")
                else:
                    print("Ця модель уже вибрана.")
            elif choice == "0":
                print("До побачення!")
                break
            else:
                print("Невірний вибір, введіть 0-4.")
        except (KeyboardInterrupt, EOFError):
            print("\nПерервано.")
            break
        except Exception as e:
            print(f"Непередбачена помилка: {e}")


if __name__ == "__main__":
    main()