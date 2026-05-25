#!/usr/bin/env python3
"""Fill locale/bg/LC_MESSAGES/django.po msgstr from a mapping (run after makemessages)."""

from __future__ import annotations

from pathlib import Path

import polib

ROOT = Path(__file__).resolve().parents[1]
PO_PATH = ROOT / "locale" / "bg" / "LC_MESSAGES" / "django.po"

# English msgid -> Bulgarian (UTF-8)
BG: dict[str, str] = {
    "Client name": "Име на клиент",
    "Address": "Адрес",
    "Phone": "Телефон",
    "This field is required.": "Това поле е задължително.",
    'Client "%(name)s" was deleted.': 'Клиентът "%(name)s" беше изтрит.',
    "Company name": "Име на фирмата",
    "VAT number": "ДДС номер",
    "Registration number": "ЕИК / регистрационен номер",
    "Address line 1": "Адрес, ред 1",
    "Address line 2": "Адрес, ред 2",
    "City": "Град",
    "Postal code": "Пощенски код",
    "Country": "Държава",
    "Email": "Имейл",
    "Company logo": "Лого на фирмата",
    "Logo must be PNG, JPEG, or WEBP.": "Логото трябва да е PNG, JPEG или WEBP.",
    "Logo must be 5 MB or smaller.": "Логото трябва да е до 5 MB.",
    "Offers": "Оферти",
    "Newest first. Empty drafts with no details are hidden.": "Първо най-новите. Празни чернови без данни са скрити.",
    "Issuer:": "Издател:",
    "No company profile yet.": "Все още няма фирмен профил.",
    "Set up profile": "Настрой профил",
    "Offer #%(n)s": "Оферта №%(n)s",
    "Draft": "Чернова",
    "1 line · updated %(d)s": "1 ред · обновена %(d)s",
    "%(c)s lines · updated %(d)s": "%(c)s реда · обновена %(d)s",
    "View": "Преглед",
    "No offers to show yet.": "Все още няма оферти за показване.",
    "Create an offer": "Създай оферта",
    "or save header details / add a line so a draft appears here.": "или запази данните в заглавката / добави ред, за да се появи чернова тук.",
    "Pagination": "Страниране",
    "Page %(p)s of %(t)s": "Страница %(p)s от %(t)s",
    "Previous": "Предишна",
    "Next": "Следваща",
    "Issuer": "Издател",
    "All offers": "Всички оферти",
    "Dashboard": "Табло",
    "Recent offers": "Скорошни оферти",
    "No other offers yet.": "Все още няма други оферти.",
    "Product catalog": "Каталог продукти",
    "Search products": "Търсене на продукти",
    "Search (min. 3 characters)…": "Търсене (минимум 3 знака)…",
    "BGN": "лв.",
    "Add to offer": "Добави към офертата",
    "No catalog items.": "Няма артикули в каталога.",
    "New offer": "Нова оферта",
    (
        "Line items save automatically when you add or edit rows. Click Save offer to "
        "store client and offer details (this creates the offer if it does not exist "
        "yet)."
    ): (
        "Редовете се записват автоматично при добавяне или редакция. Натисни "
        "„Запази оферта“, за да запазиш клиент и данни за офертата (създава офертата, ако "
        "още не съществува)."
    ),
    "Client": "Клиент",
    "Type to search or enter a new name…": "Търси или въведи ново име…",
    "Site address": "Адрес на обекта",
    "Offer date": "Дата на офертата",
    "Validity": "Валидност",
    "Save offer": "Запази оферта",
    "Download PDF": "Изтегли PDF",
    "Description": "Описание",
    "Qty": "Кол.",
    "Unit price": "Ед. цена",
    "VAT %": "ДДС %",
    "Total": "Общо",
    "No lines yet. Add a product from the catalog.": "Все още няма редове. Добави продукт от каталога.",
    "Subtotal (ex VAT)": "Сума без ДДС",
    "VAT": "ДДС",
    "—": "—",
    "7 days": "7 дни",
    "14 days": "14 дни",
    "30 days": "30 дни",
    "60 days": "60 дни",
    "Saved.": "Запазено.",
    "Could not start offer.": "Неуспешно стартиране на оферта.",
    "Save failed.": "Запазването не бе успешно.",
    "Request failed.": "Заявката не бе успешна.",
    "Validation error.": "Грешка при валидация.",
    "Remove line": "Премахни ред",
    "Offer %(id)s": "Оферта %(id)s",
    "Offer": "Оферта",
    "Offer #%(id)s": "Оферта №%(id)s",
    "Details": "Данни",
    "Line items": "Редове",
    "Unit": "Мярка",
    "Net": "Нето",
    "Totals": "Обобщение",
    "Total (incl. VAT)": "Обща сума (с ДДС)",
    "Name": "Име",
    "Base price": "Базова цена",
    "VAT rate (%)": "ДДС ставка (%)",
    "Base price cannot be negative.": "Базовата цена не може да е отрицателна.",
    "VAT rate must be between 0 and 100.": "ДДС ставката трябва да е между 0 и 100.",
    'Cannot delete "%(name)s" because it is used on one or more offers.': "Не може да се изтрие „%(name)s“, защото се използва в една или повече оферти.",
    'Catalog item "%(name)s" was deleted.': "Артикулът „%(name)s“ беше изтрит.",
    "Offer Builder": "Конструктор на оферти",
    "Clients": "Клиенти",
    "Catalog": "Каталог",
    "Company": "Фирма",
    "Logout": "Изход",
    "Bulgarian": "Български",
    "English": "Английски",
    "Read-only summary": "Обобщение (само за четене)",
    "Open in builder": "Отвори в редактора",
    "No line items.": "Няма редове.",
    "Line total": "Ред общо",
    "Back to offers": "Към офертите",
    "Client companies": "Клиентски фирми",
    "Recipients you prepare offers for.": "Получатели, за които подготвяте оферти.",
    "Add client": "Добави клиент",
    "Edit": "Редакция",
    "Delete this client? Offers that used them will keep their other data; the client link will be cleared.": "Изтриване на този клиент? Офертите, които са го ползвали, запазват останалите данни; връзката към клиента се изчиства.",
    "Delete": "Изтриване",
    "No clients yet.": "Все още няма клиенти.",
    "Add your first client": "Добави първи клиент",
    "Only the client name is required.": "Задължително е само името на клиента.",
    "Cancel": "Отказ",
    "Product / service catalog": "Каталог продукти / услуги",
    "Base price, VAT %, and computed final price per unit.": "Базова цена, ДДС % и изчислена крайна цена за единица.",
    "Add item": "Добави артикул",
    "Unit:": "Мярка:",
    "Base:": "База:",
    "Final:": "Крайна:",
    "Delete this catalog item? This cannot be undone if the item is not used on any offer.": "Изтриване на този артикул от каталога? Не може да се отмени, ако артикулът не се ползва в оферта.",
    "No catalog items yet.": "Все още няма артикули в каталога.",
    "Add your first item": "Добави първи артикул",
    "Choose a unit (брой, м², or м). Final price = base price × (1 + VAT% / 100), rounded to two decimals.": "Изберете мярка (брой, м² или м). Крайна цена = базова × (1 + ДДС% / 100), закръглена до втори знак.",
    "Current final price (computed):": "Текуща крайна цена (изчислена):",
    "Main Company Profile": "Основен фирмен профил",
    "Issuer details reused across all offers.": "Данни за издателя, ползвани във всички оферти.",
    "Allowed: PNG/JPEG/WEBP up to 5 MB.": "Позволено: PNG/JPEG/WEBP до 5 MB.",
    "Current logo": "Текущо лого",
    "Current company logo": "Текущо лого на фирмата",
    "Save profile": "Запази профил",
    "Operator login": "Вход за оператор",
    "Sign in to manage offers and products/services.": "Влезте, за да управлявате оферти и продукти/услуги.",
    "Please enter a correct username and password.": "Въведете коректно потребителско име и парола.",
    "Username": "Потребителско име",
    "Password": "Парола",
    "Sign in": "Вход",
    "Forgot password?": "Забравена парола?",
    "Reset your password": "Нулиране на парола",
    "Enter your operator email to receive a reset link.": "Въведете имейла на оператора, за да получите линк за нулиране.",
    "Send reset link": "Изпрати линк",
    "Check your email": "Проверете имейла",
    "If an account exists for that email, we sent instructions to reset your password.": "Ако има акаунт за този имейл, изпратихме инструкции за нулиране на паролата.",
    "Back to login": "Към входа",
    "Password updated": "Паролата е обновена",
    "Your password has been changed successfully.": "Паролата ви беше променена успешно.",
    "Sign in now": "Влез сега",
    "Set a new password": "Задай нова парола",
    "Save new password": "Запази новата парола",
    "This reset link is invalid or has already been used.": "Този линк е невалиден или вече е използван.",
    "Add client company": "Добави клиентска фирма",
    "Create": "Създай",
    "Edit client company": "Редакция на клиентска фирма",
    "Save": "Запази",
    "Add catalog item": "Добави артикул в каталога",
    "Edit catalog item": "Редакция на артикул",
    "VAT:": "ДДС:",
    "Reg.:": "Рег.:",
    "Base price, VAT rate, and computed final price per unit.": "Базова цена, ставка на ДДС и изчислена крайна цена за единица.",
    (
        "Choose a unit (piece, m², or m). Final price is base price times one plus VAT over 100, "
        "rounded to two decimals."
    ): (
        "Изберете мярка (брой, м² или м). Крайната цена е базовата цена по (1 + ДДС/100), "
        "закръглена до втори знак."
    ),
    "Client:": "Клиент:",
    "Site:": "Обект:",
    "Date:": "Дата:",
    "Validity:": "Валидност:",
    "Units": "Мерни единици",
    "Manage measurement units used in product catalog items.": "Управлявай мерните единици, използвани в артикулите от каталога.",
    "Add unit": "Добави мерна единица",
    "Code:": "Код:",
    "Sort:": "Ред:",
    "Delete this unit? This cannot be undone if the unit is not used by any catalog item.": "Изтриване на тази мерна единица? Не може да се отмени, ако единицата не се използва в артикул от каталога.",
    "No units yet.": "Все още няма мерни единици.",
    "Add your first unit": "Добави първа мерна единица",
    "Back to catalog": "Към каталога",
    "Set a unit label and display order. Code is generated automatically.": "Задай име на мерната единица и ред на показване. Кодът се генерира автоматично.",
    "Label (Bulgarian)": "Име (на български)",
    "Sort order": "Ред на показване",
    'Unit "%(name)s" was created.': 'Мерната единица "%(name)s" е създадена.',
    "Edit unit": "Редакция на мерна единица",
    'Unit "%(name)s" was updated.': 'Мерната единица "%(name)s" е обновена.',
    'Cannot delete unit "%(name)s" because it is used by one or more catalog items.': 'Не може да се изтрие мерната единица "%(name)s", защото се използва в един или повече артикули от каталога.',
    'Unit "%(name)s" was deleted.': 'Мерната единица "%(name)s" беше изтрита.',
}


def main() -> None:
    po = polib.pofile(str(PO_PATH))
    for entry in po:
        if entry.msgid in BG:
            entry.msgstr = BG[entry.msgid]
        elif entry.msgid:
            # Leave empty -> gettext falls back to msgid; prefer explicit copy for stability
            entry.msgstr = entry.msgid
    po.metadata["Language"] = "bg"
    if "Language-Team" not in po.metadata:
        po.metadata["Language-Team"] = "Bulgarian <bg@li.org>"
    for entry in po:
        if entry.msgid == "\u2014":  # em dash placeholder
            entry.msgstr = "\u2014"
    po.save(str(PO_PATH))
    print(f"Updated {len(po)} entries in {PO_PATH}")


if __name__ == "__main__":
    main()
