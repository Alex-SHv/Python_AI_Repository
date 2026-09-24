import docx

# Список спам-слов (можно дополнять)
spamWords = [
    "миллион",
    "выиграли",
    "выигрывать",
    "бесплатно",
    "казино",
    "таблетки",
    "кредит",
    "виагра",
    "заработок",
    "срочно",
    "приз",
    "поздравляем",
    "подтвердите",
    "подтверждение",
    "скидка",
    "сегодня",
    "немедленно",
    "бонус",
    "подарок",
    "лотерея",
    "распродажа",
    "промокод",
    "акция",
    "активируйте",
    "истекает"
]


def read_emails(filename):
    """Читает emails.docx и возвращает список писем (словарей from/text/date)."""
      # библиотека python-docx

    emails = []
    current = {}

    doc = docx.Document(filename)

    for paragraph in doc.paragraphs:
        line = paragraph.text.strip()

        if not line:
            # Пустая строка = конец письма
            if current:
                emails.append(current)
                current = {}
            continue

        if line.lower().startswith("from:"):
            current["from"] = line[5:].strip()
        elif line.lower().startswith("text:"):
            current["text"] = line[5:].strip()
        elif line.lower().startswith("date:"):
            current["date"] = line[5:].strip()

    # Не забыть последнее письмо, если файл не кончается пустым абзацем
    if current:
        emails.append(current)

    return emails


def is_spam(email, spam_words):
    """Проверяет, содержит ли текст письма спам-слова."""
    text = email.get("text", "").lower()
    for word in spam_words:
        if word.lower() in text:
            return True
    return False


def write_email(f, email):
    """Записывает письмо в читаемом формате."""
    f.write(f"from: {email.get('from', '')}\n")
    f.write(f"text: {email.get('text', '')}\n")
    f.write(f"date: {email.get('date', '')}\n")
    f.write("\n")


def main():
    emails = read_emails("emails.docx")

    spam_count = 0
    not_spam_count = 0

    with open("spam.txt", "w", encoding="utf-8") as spam_file, \
         open("NotSpam.txt", "w", encoding="utf-8") as notspam_file:

        for email in emails:
            if is_spam(email, spamWords):
                write_email(spam_file, email)
                spam_count += 1
            else:
                write_email(notspam_file, email)
                not_spam_count += 1

    print(f"Обработано писем: {len(emails)}")
    print(f"Спам: {spam_count} -> spam.txt")
    print(f"Не спам: {not_spam_count} -> NotSpam.txt")


if __name__ == "__main__":
    main()
