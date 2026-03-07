from __future__ import annotations

from typing import Any

from app.constants import CHECKLIST_ITEMS


DEFAULT_LANGUAGE = "ru"
SUPPORTED_LANGUAGES = {"ru", "tg", "uz"}

BACK_LABELS = {
    "ru": "Назад",
    "tg": "Бозгашт",
    "uz": "Ortga",
}

DRIVER_LICENSE_TYPE_LABELS_I18N = {
    "ru": {
        "ru_by": "РФ и Беларусь",
        "foreign": "Иностранные",
    },
    "tg": {
        "ru_by": "Русия ва Беларус",
        "foreign": "Хориҷӣ",
    },
    "uz": {
        "ru_by": "Rossiya va Belarus",
        "foreign": "Chet el",
    },
}

REQUIRED_PHOTO_LABELS_I18N = {
    "ru": {
        "front": "Фото спереди",
        "rear": "Фото сзади",
        "left": "Фото слева",
        "right": "Фото справа",
        "dashboard": "Фото приборной панели",
    },
    "tg": {
        "front": "Акси пеш",
        "rear": "Акси қафо",
        "left": "Акси чап",
        "right": "Акси рост",
        "dashboard": "Акси панели асбобҳо",
    },
    "uz": {
        "front": "Old tomondan foto",
        "rear": "Orqa tomondan foto",
        "left": "Chap tomondan foto",
        "right": "O'ng tomondan foto",
        "dashboard": "Panel fotosi",
    },
}

CHECKLIST_ITEMS_I18N = {
    "ru": CHECKLIST_ITEMS,
    "tg": [
        "Мавҷудияти ҳуҷҷатҳо ва корт (ВУ, СТС, ОСАГО, варақаи роҳ, корти сӯзишворӣ)",
        "Сатҳи равған дар муҳаррик / қуттии интиқол",
        "Сатҳи моеъи хунуккунанда",
        "Фишор дар шинаҳо",
        "Солимии низоми тормоз",
        "Солимии чароғҳои пеш / чароғҳои паҳлӯӣ",
        "Тозагии кабина ва кузов / маҷмӯи калидҳо",
    ],
    "uz": [
        "Hujjatlar va karta mavjudligi (VU, STS, OSAGO, yo'l varaqasi, yoqilg'i kartasi)",
        "Dvigatel / uzatmalar qutisidagi moy darajasi",
        "Sovitish suyuqligi darajasi",
        "Shinalardagi bosim",
        "Tormoz tizimi sozligi",
        "Faralar / gabarit chiroqlar sozligi",
        "Kabina va kuzov tozaligi / kalitlar to'plami",
    ],
}

CHECKLIST_ITEMS_FOREIGN_I18N = {
    "ru": [
        "Наличие документов и карты (ВУ, СТС, ОСАГО, топливная карта)",
        "Уровень масла в двигателе / КПП",
        "Уровень охлаждающей жидкости",
        "Давление в шинах",
        "Исправность тормозной системы",
        "Исправность фар / габаритных огней",
        "Чистота кабины и кузова / набор ключей",
    ],
    "tg": [
        "Мавҷудияти ҳуҷҷатҳо ва корт (ВУ, СТС, ОСАГО, корти сӯзишворӣ)",
        "Сатҳи равған дар муҳаррик / қуттии интиқол",
        "Сатҳи моеъи хунуккунанда",
        "Фишор дар шинаҳо",
        "Солимии низоми тормоз",
        "Солимии чароғҳои пеш / чароғҳои паҳлӯӣ",
        "Тозагии кабина ва кузов / маҷмӯи калидҳо",
    ],
    "uz": [
        "Hujjatlar va karta mavjudligi (VU, STS, OSAGO, yoqilg'i kartasi)",
        "Dvigatel / uzatmalar qutisidagi moy darajasi",
        "Sovitish suyuqligi darajasi",
        "Shinalardagi bosim",
        "Tormoz tizimi sozligi",
        "Faralar / gabarit chiroqlar sozligi",
        "Kabina va kuzov tozaligi / kalitlar to'plami",
    ],
}

SPECIAL_CHECKLIST_EQUIPMENT_TYPES = {
    "Фронтальные погрузчики",
    "Минипогрузчики",
    "Мини погрузчики",
    "Экскаваторы погрузчики",
    "Асфальтоукладчики",
    "Фрезы",
}

SPECIAL_CHECKLIST_WITHOUT_JOINTS_TYPES = {
    "Асфальтоукладчики",
    "Фрезы",
}

DUMP_TRUCK_EQUIPMENT_TYPE = "Самосвалы"

DUMP_TRUCK_TENT_ITEM_I18N = {
    "ru": "Самосвал: наличие палатки",
    "tg": "Самосвал: мавҷудияти палатка",
    "uz": "Samosval: tent mavjudligi",
}

CHECKLIST_ITEMS_ROLLERS_I18N = {
    "ru": [
        "Уровень масла в моторе / гидравлическое масло",
        "Уровень охлаждающей жидкости",
        "Состояние вальцов и резинометаллических блоков",
        "Смазка и наличие шприца",
        "Исправность тормозной системы",
        "Фары / габаритные огни",
        "Чистота кабины и моторного отсека / набора ключей",
        "Состояние системы орошения (чистота фильтра и рабочее состояние насоса)",
        "Состояние соединений (палец, втулка)",
    ],
    "tg": [
        "Сатҳи равған дар муҳаррик / равғани гидравликӣ",
        "Сатҳи моеъи хунуккунанда",
        "Ҳолати валецҳо ва блокҳои резина-металлӣ",
        "Молидан ва мавҷудияти шприц",
        "Солимии низоми тормоз",
        "Чароғҳои пеш / чароғҳои паҳлӯӣ",
        "Тозагии кабина ва қисмати муҳаррик / маҷмӯи калидҳо",
        "Ҳолати низоми обпошӣ (тозагии филтр ва ҳолати кории насос)",
        "Ҳолати пайвастҳо (палец, втулка)",
    ],
    "uz": [
        "Dvigateldagi moy darajasi / gidravlik moy",
        "Sovutish suyuqligi darajasi",
        "Valetslar va rezina-metall bloklar holati",
        "Moylash va shprits mavjudligi",
        "Tormoz tizimi sozligi",
        "Faralar / gabarit chiroqlar",
        "Kabina va dvigatel bo'limi tozaligi / kalitlar to'plami",
        "Sug'orish tizimi holati (filtr tozaligi va nasosning ishchi holati)",
        "Ulanishlar holati (palets, vtulka)",
    ],
}

CHECKLIST_ITEMS_SPECIAL_I18N = {
    "ru": [
        "Уровень масла в моторе / гидравлическое масло",
        "Уровень охлаждающей жидкости",
        "Состояние ходовой части (пневмошины/гусеничная цепь, башмаки)",
        "Смазка и наличие шприца",
        "Исправность тормозной системы",
        "Фары / габаритные огни",
        "Чистота кабины и моторного отсека, набор ключей",
        "Рабочий орган (ковши, отбойники, метла и т.д.)",
        "Состояние расходников (зубья, лезвие ковша)",
        "Состояние соединений (палец, втулка)",
    ],
    "tg": [
        "Сатҳи равған дар муҳаррик / равғани гидравликӣ",
        "Сатҳи моеъи хунуккунанда",
        "Ҳолати қисми ҳаракаткунанда (шинаҳои пневматикӣ/занҷири гусеничӣ, башмакҳо)",
        "Молидан ва мавҷудияти шприц",
        "Солимии низоми тормоз",
        "Чароғҳои пеш / чароғҳои паҳлӯӣ",
        "Тозагии кабина ва қисмати муҳаррик, маҷмӯи калидҳо",
        "Таҷҳизоти корӣ (ковшҳо, отбойникҳо, ҷорӯб ва ғайра)",
        "Ҳолати масрафшавандаҳо (дандонҳо, теғи ковш)",
        "Ҳолати пайвастҳо (палец, втулка)",
    ],
    "uz": [
        "Dvigateldagi moy darajasi / gidravlik moy",
        "Sovutish suyuqligi darajasi",
        "Yurish qismi holati (pnevmoshinalar/gusenitsa zanjiri, bashmaklar)",
        "Moylash va shprits mavjudligi",
        "Tormoz tizimi sozligi",
        "Faralar / gabarit chiroqlar",
        "Kabina va dvigatel bo'limi tozaligi, kalitlar to'plami",
        "Ishchi organ (kovshlar, otboyniklar, supurgi va h.k.)",
        "Sarf materiallari holati (tishlar, kovsh tig'i)",
        "Ulanishlar holati (palets, vtulka)",
    ],
}

CHECKLIST_ITEMS_SPECIAL_WITHOUT_JOINTS_I18N = {
    "ru": [
        "Уровень масла в моторе / гидравлическое масло",
        "Уровень охлаждающей жидкости",
        "Состояние ходовой части (пневмошины/гусеничная цепь, башмаки)",
        "Смазка и наличие шприца",
        "Исправность тормозной системы",
        "Фары / габаритные огни",
        "Чистота кабины и моторного отсека, набор ключей",
        "Рабочий орган (ковши, отбойники, метла и т.д.)",
        "Состояние расходников (зубья, лезвие ковша)",
        "Пульты управления, датчики нивелирования",
    ],
    "tg": [
        "Сатҳи равған дар муҳаррик / равғани гидравликӣ",
        "Сатҳи моеъи хунуккунанда",
        "Ҳолати қисми ҳаракаткунанда (шинаҳои пневматикӣ/занҷири гусеничӣ, башмакҳо)",
        "Молидан ва мавҷудияти шприц",
        "Солимии низоми тормоз",
        "Чароғҳои пеш / чароғҳои паҳлӯӣ",
        "Тозагии кабина ва қисмати муҳаррик, маҷмӯи калидҳо",
        "Таҷҳизоти корӣ (ковшҳо, отбойникҳо, ҷорӯб ва ғайра)",
        "Ҳолати масрафшавандаҳо (дандонҳо, теғи ковш)",
        "Пултҳои идоракунӣ, датчикҳои нивелиркунӣ",
    ],
    "uz": [
        "Dvigateldagi moy darajasi / gidravlik moy",
        "Sovutish suyuqligi darajasi",
        "Yurish qismi holati (pnevmoshinalar/gusenitsa zanjiri, bashmaklar)",
        "Moylash va shprits mavjudligi",
        "Tormoz tizimi sozligi",
        "Faralar / gabarit chiroqlar",
        "Kabina va dvigatel bo'limi tozaligi, kalitlar to'plami",
        "Ishchi organ (kovshlar, otboyniklar, supurgi va h.k.)",
        "Sarf materiallari holati (tishlar, kovsh tig'i)",
        "Boshqaruv pultlari, nivelirlash datchiklari",
    ],
}

EQUIPMENT_TYPE_LABELS_I18N = {
    "ru": {
        "Малотоннажные автомобили": "Малотоннажные автомобили",
        "Автобусы": "Автобусы",
        "Автомобили специальные": "Автомобили специальные",
        "Самосвалы": "Самосвалы",
        "Седельные тягачи": "Седельные тягачи",
        "Фронтальные погрузчики": "Фронтальные погрузчики",
        "Минипогрузчики": "Минипогрузчики",
        "Экскаваторы погрузчики": "Экскаваторы погрузчики",
        "Экскаваторы": "Экскаваторы",
        "Катки": "Катки",
        "Асфальтоукладчики": "Асфальтоукладчики",
        "Фрезы": "Фрезы",
    },
    "tg": {
        "Малотоннажные автомобили": "Мошинҳои сабукбор",
        "Автобусы": "Автобусҳо",
        "Автомобили специальные": "Автомобилҳои махсус",
        "Самосвалы": "Самосвалҳо",
        "Седельные тягачи": "Тягачҳои седелӣ",
        "Фронтальные погрузчики": "Боркунакҳои фронталӣ",
        "Минипогрузчики": "Миниборкунакҳо",
        "Экскаваторы погрузчики": "Экскаватор-боркунакҳо",
        "Экскаваторы": "Экскаваторҳо",
        "Катки": "Катокҳо",
        "Асфальтоукладчики": "Асфалтпаҳнкунандаҳо",
        "Фрезы": "Фрезаҳо",
    },
    "uz": {
        "Малотоннажные автомобили": "Yengil yuk avtomobillari",
        "Автобусы": "Avtobuslar",
        "Автомобили специальные": "Maxsus avtomobillar",
        "Самосвалы": "Samosvallar",
        "Седельные тягачи": "Sedel tyagachlar",
        "Фронтальные погрузчики": "Frontal yuklagichlar",
        "Минипогрузчики": "Mini yuklagichlar",
        "Экскаваторы погрузчики": "Ekskavator-yuklagichlar",
        "Экскаваторы": "Ekskavatorlar",
        "Катки": "Katoklar",
        "Асфальтоукладчики": "Asfalt yotqizgichlar",
        "Фрезы": "Frezalar",
    },
}

DRIVER_STATUS_TEXT_I18N = {
    "ru": {
        "approved": "Проверка принята. Выезд разрешен.",
        "rejected": "Выезд запрещен. Подойти к механику.",
        "repair": "Техника отправлена в ремонт. Подойти к механику.",
    },
    "tg": {
        "approved": "Санҷиш қабул шуд. Баромадан иҷозат аст.",
        "rejected": "Баромадан манъ аст. Ба назди механик равед.",
        "repair": "Техника ба таъмир фиристода шуд. Ба назди механик равед.",
    },
    "uz": {
        "approved": "Tekshiruv qabul qilindi. Chiqishga ruxsat berildi.",
        "rejected": "Chiqish taqiqlandi. Mexanik oldiga boring.",
        "repair": "Texnika ta'mirga yuborildi. Mexanik oldiga boring.",
    },
}

TEXTS = {
    "choose_language_prompt": {
        "ru": "Выберите язык интерфейса:",
        "tg": "Забони интерфейсро интихоб кунед:",
        "uz": "Interfeys tilini tanlang:",
    },
    "choose_language_buttons_hint": {
        "ru": "Пожалуйста, выберите язык кнопками ниже.",
        "tg": "Лутфан забонро бо тугмаҳои поён интихоб кунед.",
        "uz": "Iltimos, tilni quyidagi tugmalar orqali tanlang.",
    },
    "language_saved": {
        "ru": "Язык сохранен ✅",
        "tg": "Забон сабт шуд ✅",
        "uz": "Til saqlandi ✅",
    },
    "registration_start": {
        "ru": "Перед началом работы нужно пройти регистрацию сотрудника.\nВведите ФИО полностью (например: Иванов Иван Иванович).",
        "tg": "Пеш аз оғози кор сабти номи корманд лозим аст.\nНому насабро пурра ворид кунед (масалан: Иванов Иван Иванович).",
        "uz": "Ishni boshlashdan oldin xodim ro'yxatdan o'tishi kerak.\nF.I.Sh.ni to'liq kiriting (masalan: Ivanov Ivan Ivanovich).",
    },
    "registration_consent_prompt": {
        "ru": "Нажимая кнопку «Согласен на обработку персональных данных», вы даёте согласие на обработку персональных данных (ФИО, номер телефона, фотографии, геолокация) для оформления заявки.",
        "tg": "Бо пахши тугмаи «Ба коркарди маълумоти шахсӣ розӣ ҳастам», шумо ба коркарди маълумоти шахсӣ (Ному насаб, рақами телефон, аксҳо, геолокатсия) барои тартиб додани дархост розигӣ медиҳед.",
        "uz": "«Shaxsiy ma'lumotlarni qayta ishlashga roziman» tugmasini bosib, ariza rasmiylashtirish uchun shaxsiy ma'lumotlaringizni (F.I.Sh., telefon raqami, fotosuratlar, geolokatsiya) qayta ishlashga rozilik berasiz.",
    },
    "registration_consent_policy_hint": {
        "ru": "Перед согласием ознакомьтесь с политикой персональных данных по кнопке ниже.",
        "tg": "Пеш аз розигӣ бо сиёсати маълумоти шахсӣ аз тугмаи поён шинос шавед.",
        "uz": "Rozilik berishdan oldin quyidagi tugma orqali shaxsiy ma'lumotlar siyosati bilan tanishing.",
    },
    "registration_consent_policy_button": {
        "ru": "Ознакомиться с политикой персональных данных",
        "tg": "Шиносоӣ бо сиёсати маълумоти шахсӣ",
        "uz": "Shaxsiy ma'lumotlar siyosati bilan tanishish",
    },
    "registration_consent_agree_button": {
        "ru": "Согласен на обработку персональных данных",
        "tg": "Ба коркарди маълумоти шахсӣ розӣ ҳастам",
        "uz": "Shaxsiy ma'lumotlarni qayta ishlashga roziman",
    },
    "registration_consent_decline_button": {
        "ru": "Не согласен",
        "tg": "Розӣ нестам",
        "uz": "Rozi emasman",
    },
    "registration_consent_buttons_hint": {
        "ru": "Для продолжения выберите вариант кнопками ниже.",
        "tg": "Барои идома, яке аз тугмаҳои поёнро интихоб кунед.",
        "uz": "Davom etish uchun quyidagi tugmalardan birini tanlang.",
    },
    "registration_consent_accepted": {
        "ru": "Согласие сохранено ✅",
        "tg": "Розигӣ сабт шуд ✅",
        "uz": "Rozilik saqlandi ✅",
    },
    "registration_consent_declined": {
        "ru": "Вы отказались от обработки персональных данных. Дальнейшая работа с ботом недоступна, пока не дадите согласие через /start или /register.",
        "tg": "Шумо аз коркарди маълумоти шахсӣ даст кашидед. Кори минбаъда бо бот дастнорас аст, то замоне ки бо /start ё /register розигӣ надиҳед.",
        "uz": "Siz shaxsiy ma'lumotlarni qayta ishlashdan bosh tortdingiz. /start yoki /register orqali rozilik bermaguningizcha bot bilan keyingi ishlash mumkin emas.",
    },
    "consent_required_before_registration": {
        "ru": "Сначала дайте согласие на обработку персональных данных через /start или /register.",
        "tg": "Аввал бо /start ё /register ба коркарди маълумоти шахсӣ розигӣ диҳед.",
        "uz": "Avval /start yoki /register orqali shaxsiy ma'lumotlarni qayta ishlashga rozilik bering.",
    },
    "consent_interaction_blocked_short": {
        "ru": "Нужно согласие на обработку данных. Используйте /start или /register.",
        "tg": "Розигӣ ба коркарди маълумот лозим аст. /start ё /register-ро истифода баред.",
        "uz": "Ma'lumotlarni qayta ishlashga rozilik kerak. /start yoki /register dan foydalaning.",
    },
    "start_new_inspection": {
        "ru": "Начинаем новую приемку.",
        "tg": "Қабули нави техникаро оғоз мекунем.",
        "uz": "Yangi qabulni boshlaymiz.",
    },
    "help_text": {
        "ru": "Команды:\n/start — начать новую приемку\n/endday — завершение смены\n/register — пройти или обновить регистрацию\n/actions — меню «Действия в течении смены»\n/help — помощь\n/role — показать вашу роль\n/setrole <telegram_id> <role> — назначить роль (только superadmin)\nРоли: driver, mechanic, admin, superadmin",
        "tg": "Фармонҳо:\n/start — оғози қабули нав\n/endday — анҷоми рӯзи корӣ\n/register — сабти ном ё навсозӣ\n/actions — менюи «Амалҳо дар ҷараёни рӯз»\n/help — кӯмак\n/role — нишон додани нақш\n/setrole <telegram_id> <role> — таъини нақш (танҳо superadmin)\nНақшҳо: driver, mechanic, admin, superadmin",
        "uz": "Buyruqlar:\n/start — yangi qabulni boshlash\n/endday — ish kunini yakunlash\n/register — ro'yxatdan o'tish yoki yangilash\n/actions — «Kun davomida harakatlar» menyusi\n/help — yordam\n/role — rolingizni ko'rsatish\n/setrole <telegram_id> <role> — rol berish (faqat superadmin)\nRollar: driver, mechanic, admin, superadmin",
    },
    "daily_actions_menu_button": {
        "ru": "🗂️ Действия в течении смены",
        "tg": "🗂️ Амалҳо дар ҷараёни рӯз",
        "uz": "🗂️ Kun davomida harakatlar",
    },
    "daily_actions_open_prompt": {
        "ru": "Меню действий открыто. Нажмите кнопку ниже.",
        "tg": "Менюи амалҳо кушода шуд. Тугмаи поёнро пахш кунед.",
        "uz": "Harakatlar menyusi ochildi. Quyidagi tugmani bosing.",
    },
    "daily_actions_open_buttons_hint": {
        "ru": "Выберите действие кнопкой ниже.",
        "tg": "Амалро бо тугмаи поён интихоб кунед.",
        "uz": "Amalni quyidagi tugma orqali tanlang.",
    },
    "daily_actions_submenu_prompt": {
        "ru": "Выберите подпункт «Действия в течении смены»:",
        "tg": "Зербанди «Амалҳо дар ҷараёни рӯз»-ро интихоб кунед:",
        "uz": "«Kun davomida harakatlar» bo'limidan tanlang:",
    },
    "daily_actions_submenu_buttons_hint": {
        "ru": "Выберите один из подпунктов кнопками.",
        "tg": "Яке аз зербандҳоро бо тугмаҳо интихоб кунед.",
        "uz": "Tugmalar orqali bo'limlardan birini tanlang.",
    },
    "daily_action_blow_filters": {
        "ru": "💨 Продувка Фильтров",
        "tg": "💨 Тозакунии филтрҳо",
        "uz": "💨 Filtrlarni tozalash",
    },
    "daily_action_workday_situations": {
        "ru": "⚠️ Ситуации в течении рабочего дня",
        "tg": "⚠️ Ҳолатҳо дар ҷараёни рӯзи корӣ",
        "uz": "⚠️ Ish kuni davomida vaziyatlar",
    },
    "daily_action_refuel": {
        "ru": "⛽ Заправка ГСМ",
        "tg": "⛽ Пуркунии сӯзишворӣ",
        "uz": "⛽ Yoqilg'i quyish",
    },
    "daily_action_end_workday": {
        "ru": "🏁 Завершение смены",
        "tg": "🏁 Анҷоми рӯзи корӣ",
        "uz": "🏁 Ish kunini yakunlash",
    },
    "daily_action_selected": {
        "ru": "Вы выбрали: {action}",
        "tg": "Шумо интихоб кардед: {action}",
        "uz": "Siz tanladingiz: {action}",
    },
    "daily_filter_result_prompt": {
        "ru": "Продувка фильтра выполнена?",
        "tg": "Тозакунии филтр иҷро шуд?",
        "uz": "Filtrni tozalash bajarildimi?",
    },
    "daily_filter_done_button": {
        "ru": "Сделал",
        "tg": "Иҷро шуд",
        "uz": "Bajarildi",
    },
    "daily_filter_not_done_button": {
        "ru": "Не сделал",
        "tg": "Иҷро нашуд",
        "uz": "Bajarilmadi",
    },
    "daily_filter_result_buttons_hint": {
        "ru": "Выберите вариант кнопками: «Сделал» или «Не сделал».",
        "tg": "Вариантро бо тугма интихоб кунед: «Иҷро шуд» ё «Иҷро нашуд».",
        "uz": "Variantni tugma orqali tanlang: «Bajarildi» yoki «Bajarilmadi».",
    },
    "daily_filter_not_done_comment_prompt": {
        "ru": "Опишите комментарий, почему продувка фильтра не выполнена.",
        "tg": "Шарҳ диҳед, чаро тозакунии филтр иҷро нашуд.",
        "uz": "Filtr tozalanmagani sababini izohlang.",
    },
    "daily_workday_comment_prompt": {
        "ru": "Опишите ситуацию в течении рабочего дня комментарием.",
        "tg": "Ҳолатро дар ҷараёни рӯзи корӣ бо шарҳ нависед.",
        "uz": "Ish kuni davomida vaziyatni izoh bilan yozing.",
    },
    "daily_comment_too_short": {
        "ru": "Комментарий слишком короткий. Напишите подробнее.",
        "tg": "Шарҳ хеле кӯтоҳ аст. Муфассалтар нависед.",
        "uz": "Izoh juda qisqa. Batafsilroq yozing.",
    },
    "daily_optional_photo_prompt": {
        "ru": "При необходимости приложите фото. Если фото не нужно, нажмите «Пропустить фото».",
        "tg": "Агар лозим бошад, акс замима кунед. Агар акс даркор набошад, «Бе акс идома додан»-ро пахш кунед.",
        "uz": "Zarur bo'lsa foto yuboring. Foto kerak bo'lmasa, «Fotosiz davom etish» ni bosing.",
    },
    "daily_skip_photo_button": {
        "ru": "Пропустить фото",
        "tg": "Бе акс идома додан",
        "uz": "Fotosiz davom etish",
    },
    "daily_waiting_photo_or_skip": {
        "ru": "Отправьте фото или нажмите «Пропустить фото».",
        "tg": "Акс фиристед ё «Бе акс идома додан»-ро пахш кунед.",
        "uz": "Foto yuboring yoki «Fotosiz davom etish» ni bosing.",
    },
    "daily_refuel_prompt": {
        "ru": "Выберите действие по заправке кнопками ниже.",
        "tg": "Амалро барои пуркунии сӯзишворӣ бо тугмаҳои поён интихоб кунед.",
        "uz": "Yoqilg'i bo'yicha amalni quyidagi tugmalar orqali tanlang.",
    },
    "daily_refuel_required_button": {
        "ru": "Требуется заправка",
        "tg": "Пуркунӣ лозим аст",
        "uz": "Yoqilg'i kerak",
    },
    "daily_refuel_completed_button": {
        "ru": "Заправка завершена",
        "tg": "Пуркунӣ анҷом шуд",
        "uz": "Yoqilg'i quyish yakunlandi",
    },
    "daily_refuel_approve_button": {
        "ru": "✅ Одобрить заправку",
        "tg": "✅ Пуркуниро тасдиқ кардан",
        "uz": "✅ Yoqilg'i quyishni tasdiqlash",
    },
    "daily_refuel_reject_button": {
        "ru": "🚫 Запретить заправку",
        "tg": "🚫 Пуркуниро манъ кардан",
        "uz": "🚫 Yoqilg'i quyishni taqiqlash",
    },
    "daily_refuel_mechanic_decision_prompt": {
        "ru": "Решение по заправке примите кнопками ниже.",
        "tg": "Қарор оид ба пуркунӣ бо тугмаҳои поён қабул кунед.",
        "uz": "Yoqilg'i bo'yicha qarorni quyidagi tugmalar bilan qabul qiling.",
    },
    "daily_refuel_buttons_hint": {
        "ru": "Выберите кнопкой: «Требуется заправка» или «Заправка завершена».",
        "tg": "Бо тугма интихоб кунед: «Пуркунӣ лозим аст» ё «Пуркунӣ анҷом шуд».",
        "uz": "Tugma bilan tanlang: «Yoqilg'i kerak» yoki «Yoqilg'i quyish yakunlandi».",
    },
    "daily_end_workday_refuel_prompt": {
        "ru": "Завершение смены: заправка ГСМ была?",
        "tg": "Анҷоми рӯзи корӣ: пуркунии сӯзишворӣ буд?",
        "uz": "Ish kunini yakunlash: yoqilg'i quyildimi?",
    },
    "daily_end_workday_refuel_yes_button": {
        "ru": "Да",
        "tg": "Ҳа",
        "uz": "Ha",
    },
    "daily_end_workday_refuel_no_button": {
        "ru": "Нет",
        "tg": "Не",
        "uz": "Yo'q",
    },
    "daily_end_workday_refuel_buttons_hint": {
        "ru": "Выберите кнопкой: «Да» или «Нет».",
        "tg": "Бо тугма интихоб кунед: «Ҳа» ё «Не».",
        "uz": "Tugma bilan tanlang: «Ha» yoki «Yo'q».",
    },
    "daily_end_workday_fuel_level_photo_prompt": {
        "ru": "Отправьте обязательное фото: Уровень топлива.",
        "tg": "Акси ҳатмиро фиристед: Сатҳи сӯзишворӣ.",
        "uz": "Majburiy foto yuboring: Yoqilg'i darajasi.",
    },
    "daily_end_workday_fuel_level_photo_waiting": {
        "ru": "Сначала отправьте обязательное фото: Уровень топлива.",
        "tg": "Аввал акси ҳатмиро фиристед: Сатҳи сӯзишворӣ.",
        "uz": "Avval majburiy fotoni yuboring: Yoqilg'i darajasi.",
    },
    "daily_end_workday_photos_intro": {
        "ru": "Отправьте 5 обязательных фото одним сообщением (альбомом) в порядке:\n- Фото спереди\n- Фото сзади\n- Фото слева\n- Фото справа\n- Фото приборной панели",
        "tg": "5 акси ҳатмиро як паём (албом) фиристед бо тартиб:\n- Акси пеш\n- Акси қафо\n- Акси чап\n- Акси рост\n- Акси панели асбобҳо",
        "uz": "5 ta majburiy fotoni bitta xabar (albom) qilib shu tartibda yuboring:\n- Old tomondan foto\n- Orqa tomondan foto\n- Chap tomondan foto\n- O'ng tomondan foto\n- Panel fotosi",
    },
    "daily_end_workday_photo_waiting": {
        "ru": "Сейчас нужно отправить 5 обязательных фото.",
        "tg": "Ҳозир 5 акси ҳатмиро фиристодан лозим аст.",
        "uz": "Hozir 5 ta majburiy fotoni yuborish kerak.",
    },
    "daily_end_workday_photo_progress": {
        "ru": "Принято фото: {label} ({received}/{total}). Осталось: {remaining}.",
        "tg": "Акс қабул шуд: {label} ({received}/{total}). Боқӣ: {remaining}.",
        "uz": "Foto qabul qilindi: {label} ({received}/{total}). Qoldi: {remaining}.",
    },
    "daily_end_workday_photo_done": {
        "ru": "Все 5 обязательных фото для завершения дня приняты ✅",
        "tg": "Ҳамаи 5 акси ҳатмӣ барои анҷоми рӯз қабул шуд ✅",
        "uz": "Ish kunini yakunlash uchun 5 ta majburiy foto qabul qilindi ✅",
    },
    "daily_end_workday_location_waiting": {
        "ru": "Теперь обязательно отправьте геолокацию кнопкой ниже.",
        "tg": "Акнун ҳатман геолокатсияро бо тугмаи поён ирсол кунед.",
        "uz": "Endi geolokatsiyani pastdagi tugma bilan majburiy yuboring.",
    },
    "daily_refuel_fuel_level_photo_prompt": {
        "ru": "Отправьте обязательное фото уровня топлива.",
        "tg": "Акси ҳатмии сатҳи сӯзишвориро фиристед.",
        "uz": "Yoqilg'i darajasining majburiy fotosini yuboring.",
    },
    "daily_refuel_fuel_level_photo_waiting": {
        "ru": "Сначала отправьте фото уровня топлива.",
        "tg": "Аввал акси сатҳи сӯзишвориро фиристед.",
        "uz": "Avval yoqilg'i darajasi fotosini yuboring.",
    },
    "daily_report_employee": {
        "ru": "Сотрудник",
        "tg": "Корманд",
        "uz": "Xodim",
    },
    "daily_report_id": {
        "ru": "ID отчета приемки",
        "tg": "ID ҳисоботи қабул",
        "uz": "Qabul hisobot ID",
    },
    "daily_report_action": {
        "ru": "Действие",
        "tg": "Амал",
        "uz": "Harakat",
    },
    "daily_report_phone": {
        "ru": "Телефон",
        "tg": "Рақами телефон",
        "uz": "Telefon",
    },
    "daily_report_status": {
        "ru": "Статус",
        "tg": "Ҳолат",
        "uz": "Holat",
    },
    "daily_report_comment": {
        "ru": "Комментарий",
        "tg": "Шарҳ",
        "uz": "Izoh",
    },
    "daily_report_time": {
        "ru": "Время",
        "tg": "Вақт",
        "uz": "Vaqt",
    },
    "daily_report_title_blow_filters": {
        "ru": "🧰 Отчет: Продувка фильтров",
        "tg": "🧰 Ҳисобот: Тозакунии филтрҳо",
        "uz": "🧰 Hisobot: Filtrlarni tozalash",
    },
    "daily_report_title_workday": {
        "ru": "⚠️ Отчет: Ситуация в течении рабочего дня",
        "tg": "⚠️ Ҳисобот: Ҳолат дар ҷараёни рӯзи корӣ",
        "uz": "⚠️ Hisobot: Ish kuni davomida vaziyat",
    },
    "daily_report_title_refuel": {
        "ru": "⛽ Отчет: Заправка ГСМ",
        "tg": "⛽ Ҳисобот: Пуркунии сӯзишворӣ",
        "uz": "⛽ Hisobot: Yoqilg'i quyish",
    },
    "daily_report_title_end_workday": {
        "ru": "🏁 Отчет: Завершение смены",
        "tg": "🏁 Ҳисобот: Анҷоми рӯзи корӣ",
        "uz": "🏁 Hisobot: Ish kunini yakunlash",
    },
    "daily_report_result_filter_done": {
        "ru": "✅ Продувка фильтров выполнена.",
        "tg": "✅ Тозакунии филтрҳо иҷро шуд.",
        "uz": "✅ Filtrlarni tozalash bajarildi.",
    },
    "daily_report_result_filter_not_done": {
        "ru": "❌ Продувка фильтров не выполнена.",
        "tg": "❌ Тозакунии филтрҳо иҷро нашуд.",
        "uz": "❌ Filtrlarni tozalash bajarilmadi.",
    },
    "daily_report_result_workday": {
        "ru": "⚠️ Зафиксирована ситуация в течении рабочего дня.",
        "tg": "⚠️ Ҳолат дар ҷараёни рӯзи корӣ сабт шуд.",
        "uz": "⚠️ Ish kuni davomida vaziyat qayd etildi.",
    },
    "daily_report_result_refuel": {
        "ru": "⛽ Требуется заправка ГСМ.",
        "tg": "⛽ Пуркунии сӯзишворӣ лозим аст.",
        "uz": "⛽ Yoqilg'i quyish kerak.",
    },
    "daily_report_result_refuel_completed": {
        "ru": "✅ Заправка ГСМ завершена.",
        "tg": "✅ Пуркунии сӯзишворӣ анҷом шуд.",
        "uz": "✅ Yoqilg'i quyish yakunlandi.",
    },
    "daily_report_result_end_workday_refuel_yes": {
        "ru": "⛽ Заправка ГСМ: да.",
        "tg": "⛽ Пуркунии сӯзишворӣ: ҳа.",
        "uz": "⛽ Yoqilg'i quyish: ha.",
    },
    "daily_report_result_end_workday_refuel_no": {
        "ru": "⛽ Заправка ГСМ: нет.",
        "tg": "⛽ Пуркунии сӯзишворӣ: не.",
        "uz": "⛽ Yoqilg'i quyish: yo'q.",
    },
    "daily_report_linked_inspection_reply": {
        "ru": "Привязка к прошлому отчету приемки выполнена (сообщение-ответ).",
        "tg": "Пайваст ба ҳисоботи қаблии қабул анҷом шуд (паёми ҷавоб).",
        "uz": "Oldingi qabul hisobotiga bog'lash bajarildi (javob xabari).",
    },
    "daily_report_linked_inspection_missing_reply": {
        "ru": "Не удалось сделать привязку сообщением-ответом: прошлый отчет приемки не найден в чате.",
        "tg": "Пайвастро бо паёми ҷавоб анҷом додан нашуд: ҳисоботи қаблии қабул дар чат ёфт нашуд.",
        "uz": "Javob xabari bilan bog'lash amalga oshmadi: oldingi qabul hisobotini chatdan topib bo'lmadi.",
    },
    "daily_report_geo": {
        "ru": "Геолокация",
        "tg": "Геолокатсия",
        "uz": "Geolokatsiya",
    },
    "daily_report_geo_map": {
        "ru": "Карта",
        "tg": "Харита",
        "uz": "Xarita",
    },
    "daily_report_photo_caption": {
        "ru": "Фото к отчету",
        "tg": "Акс ба ҳисобот",
        "uz": "Hisobotga foto",
    },
    "daily_refuel_report_not_found": {
        "ru": "Заявка на заправку не найдена.",
        "tg": "Дархости пуркунӣ ёфт нашуд.",
        "uz": "Yoqilg'i so'rovi topilmadi.",
    },
    "daily_refuel_decision_already_saved": {
        "ru": "Решение по заправке уже принято.",
        "tg": "Қарор оид ба пуркунӣ аллакай қабул шудааст.",
        "uz": "Yoqilg'i bo'yicha qaror allaqachon qabul qilingan.",
    },
    "daily_refuel_decision_saved": {
        "ru": "Решение по заправке сохранено.",
        "tg": "Қарор оид ба пуркунӣ сабт шуд.",
        "uz": "Yoqilg'i bo'yicha qaror saqlandi.",
    },
    "daily_refuel_decision_approved_label": {
        "ru": "Одобрено",
        "tg": "Тасдиқ шуд",
        "uz": "Tasdiqlandi",
    },
    "daily_refuel_decision_rejected_label": {
        "ru": "Запрещено",
        "tg": "Манъ шуд",
        "uz": "Taqiqlandi",
    },
    "daily_refuel_decision_by_mechanic": {
        "ru": "Решение по заявке ГСМ #{report_id}: <b>{decision}</b> (механик: {mechanic_name})",
        "tg": "Қарор барои дархости ГСМ #{report_id}: <b>{decision}</b> (механик: {mechanic_name})",
        "uz": "GSM so'rovi #{report_id} bo'yicha qaror: <b>{decision}</b> (mexanik: {mechanic_name})",
    },
    "daily_refuel_decision_driver": {
        "ru": "Решение по вашей заявке на заправку ГСМ: <b>{decision}</b>.",
        "tg": "Қарор оид ба дархости шумо барои пуркунии ГСМ: <b>{decision}</b>.",
        "uz": "Sizning GSM so'rovingiz bo'yicha qaror: <b>{decision}</b>.",
    },
    "daily_report_sent": {
        "ru": "Отчет отправлен в группу Механики ✅",
        "tg": "Ҳисобот ба гурӯҳи механикон фиристода шуд ✅",
        "uz": "Hisobot mexaniklar guruhiga yuborildi ✅",
    },
    "daily_report_delivery_failed": {
        "ru": "Не удалось отправить отчет в группу Механики. Попробуйте еще раз позже.",
        "tg": "Ҳисоботро ба гурӯҳи механикон фиристодан нашуд. Баъдтар боз кӯшиш кунед.",
        "uz": "Hisobotni mexaniklar guruhiga yuborib bo'lmadi. Keyinroq qayta urinib ko'ring.",
    },
    "daily_actions_closed": {
        "ru": "Меню «Действия в течении смены» закрыто.",
        "tg": "Менюи «Амалҳо дар ҷараёни рӯз» баста шуд.",
        "uz": "«Kun davomida harakatlar» menyusi yopildi.",
    },
    "your_role": {
        "ru": "Ваша роль: <b>{role}</b>",
        "tg": "Нақши шумо: <b>{role}</b>",
        "uz": "Sizning rolingiz: <b>{role}</b>",
    },
    "setrole_denied": {
        "ru": "Недостаточно прав. Команда доступна только superadmin.",
        "tg": "Ҳуқуқи кофӣ нест. Фармон танҳо барои superadmin дастрас аст.",
        "uz": "Huquq yetarli emas. Buyruq faqat superadmin uchun.",
    },
    "access_denied_whitelist": {
        "ru": "Доступ к боту ограничен. Обратитесь к администратору для добавления в список сотрудников.",
        "tg": "Дастрасӣ ба бот маҳдуд аст. Барои илова шудан ба рӯйхати кормандон ба администратор муроҷиат кунед.",
        "uz": "Botga kirish cheklangan. Xodimlar ro'yxatiga qo'shilish uchun administratorga murojaat qiling.",
    },
    "setrole_format": {
        "ru": "Формат: /setrole <telegram_id> <role>",
        "tg": "Намуна: /setrole <telegram_id> <role>",
        "uz": "Format: /setrole <telegram_id> <role>",
    },
    "setrole_success": {
        "ru": "Пользователю {target_id} назначена роль {role}.",
        "tg": "Ба корбар {target_id} нақши {role} таъин шуд.",
        "uz": "Foydalanuvchi {target_id} ga {role} roli berildi.",
    },
    "setrole_error": {
        "ru": "Ошибка назначения роли: {error}",
        "tg": "Хатои таъини нақш: {error}",
        "uz": "Rol berishda xatolik: {error}",
    },
    "nok_cancelled_choose_again": {
        "ru": "Ответ «Не ОК» отменен. Выберите вариант заново.",
        "tg": "Ҷавоби «На ОК» бекор шуд. Лутфан аз нав интихоб кунед.",
        "uz": "«OK emas» javobi bekor qilindi. Variantni qayta tanlang.",
    },
    "enter_name_again": {
        "ru": "Введите ФИО заново.",
        "tg": "Ному насабро дубора ворид кунед.",
        "uz": "F.I.Sh.ni qayta kiriting.",
    },
    "full_name_invalid": {
        "ru": "Введите ФИО полностью (минимум имя и фамилия).",
        "tg": "Ному насабро пурра ворид кунед (камаш ном ва насаб).",
        "uz": "F.I.Sh.ni to'liq kiriting (kamida ism va familiya).",
    },
    "enter_phone": {
        "ru": "Введите номер телефона для связи.\nДопустимы форматы: +79991234567, 89991234567, 8 (999) 123-45-67.\nЕсли нужно изменить ФИО, отправьте «{back_text}».",
        "tg": "Рақами телефонро барои тамос ворид кунед.\nФорматҳои иҷозашуда: +79991234567, 89991234567, 8 (999) 123-45-67.\nАгар ному насабро иваз кардан лозим бошад, «{back_text}»-ро фиристед.",
        "uz": "Bog'lanish uchun telefon raqamini kiriting.\nQabul qilinadigan formatlar: +79991234567, 89991234567, 8 (999) 123-45-67.\nAgar F.I.Sh.ni o'zgartirish kerak bo'lsa, «{back_text}» yuboring.",
    },
    "invalid_phone": {
        "ru": "Некорректный номер. Введите телефон в формате +79991234567 или 89991234567.",
        "tg": "Рақам нодуруст аст. Телефонро дар формати +79991234567 ё 89991234567 ворид кунед.",
        "uz": "Noto'g'ri raqam. Telefonni +79991234567 yoki 89991234567 formatida kiriting.",
    },
    "registration_completed": {
        "ru": "Регистрация завершена ✅",
        "tg": "Сабти ном анҷом ёфт ✅",
        "uz": "Ro'yxatdan o'tish yakunlandi ✅",
    },
    "go_to_inspection": {
        "ru": "Переходим к приемке.",
        "tg": "Ба қабули техника мегузарем.",
        "uz": "Qabul bosqichiga o'tamiz.",
    },
    "saved_use_start": {
        "ru": "Данные сохранены. Для новой приемки используйте /start",
        "tg": "Маълумот сабт шуд. Барои қабули нав /start-ро истифода баред.",
        "uz": "Ma'lumotlar saqlandi. Yangi qabul uchun /start dan foydalaning.",
    },
    "not_registered": {
        "ru": "Сотрудник не зарегистрирован. Используйте /register или /start для автоматической регистрации.",
        "tg": "Корманд сабт нашудааст. Барои сабти автоматӣ /register ё /start-ро истифода баред.",
        "uz": "Xodim ro'yxatdan o'tmagan. Avtomatik ro'yxatdan o'tish uchun /register yoki /start dan foydalaning.",
    },
    "already_first_step": {
        "ru": "Вы уже на первом шаге.",
        "tg": "Шумо аллакай дар қадами аввал ҳастед.",
        "uz": "Siz allaqachon birinchi bosqichdasiz.",
    },
    "select_driver_license_type": {
        "ru": "Выберите тип водительского удостоверения:",
        "tg": "Навъи шаҳодатномаи ронандагиро интихоб кунед:",
        "uz": "Haydovchilik guvohnomasi turini tanlang:",
    },
    "choose_driver_license_type_buttons": {
        "ru": "Выберите тип водительского удостоверения кнопками.",
        "tg": "Навъи шаҳодатномаи ронандагиро бо тугмаҳо интихоб кунед.",
        "uz": "Haydovchilik guvohnomasi turini tugmalar orqali tanlang.",
    },
    "choose_type_buttons": {
        "ru": "Выберите тип техники кнопками.",
        "tg": "Навъи техникаро бо тугмаҳо интихоб кунед.",
        "uz": "Texnika turini tugmalar orqali tanlang.",
    },
    "choose_brand_buttons": {
        "ru": "Выберите марку техники кнопками.",
        "tg": "Маркаи техникаро бо тугмаҳо интихоб кунед.",
        "uz": "Texnika markasini tugmalar orqali tanlang.",
    },
    "choose_number_buttons": {
        "ru": "Выберите номер техники кнопками.",
        "tg": "Рақами техникаро бо тугмаҳо интихоб кунед.",
        "uz": "Texnika raqamini tugmalar orqali tanlang.",
    },
    "profile_not_filled": {
        "ru": "Профиль сотрудника не заполнен. Используйте /register.",
        "tg": "Профили корманд пур нашудааст. /register-ро истифода баред.",
        "uz": "Xodim profili to'ldirilmagan. /register dan foydalaning.",
    },
    "equipment_selected_start_checklist": {
        "ru": "Техника выбрана: <b>{snapshot}</b>\nНачинаем чек-лист.",
        "tg": "Техника интихоб шуд: <b>{snapshot}</b>\nЧек-листро оғоз мекунем.",
        "uz": "Texnika tanlandi: <b>{snapshot}</b>\nChek-listni boshlaymiz.",
    },
    "short_comment": {
        "ru": "Комментарий слишком короткий. Опишите причину подробнее.",
        "tg": "Шарҳ хеле кӯтоҳ аст. Сабабро муфассалтар нависед.",
        "uz": "Izoh juda qisqa. Sababni batafsilroq yozing.",
    },
    "attach_issue_photo": {
        "ru": "При необходимости приложите фото неисправности. Если фото не нужно, нажмите «Пропустить фото».",
        "tg": "Агар лозим бошад, акси носозиро замима кунед. Агар акс даркор набошад, «Бе акс идома додан»-ро пахш кунед.",
        "uz": "Zarur bo'lsa nosozlik fotosini yuboring. Foto kerak bo'lmasa, «Fotosiz davom etish» ni bosing.",
    },
    "issue_skip_photo_button": {
        "ru": "Пропустить фото",
        "tg": "Бе акс идома додан",
        "uz": "Fotosiz davom etish",
    },
    "issue_waiting_photo_or_skip": {
        "ru": "Отправьте фото или нажмите «Пропустить фото».",
        "tg": "Акс фиристед ё «Бе акс идома додан»-ро пахш кунед.",
        "uz": "Foto yuboring yoki «Fotosiz davom etish» ni bosing.",
    },
    "follow_instructions": {
        "ru": "Используйте кнопки и инструкции бота. Для нового отчета — /start",
        "tg": "Аз тугмаҳо ва дастурҳои бот истифода баред. Барои ҳисоботи нав — /start",
        "uz": "Bot tugmalari va ko'rsatmalaridan foydalaning. Yangi hisobot uchun — /start",
    },
    "inspection_start_first": {
        "ru": "Сначала начните приемку командой /start.",
        "tg": "Аввал қабулро бо фармони /start оғоз кунед.",
        "uz": "Avval qabulni /start buyrug'i bilan boshlang.",
    },
    "issue_recorded": {
        "ru": "Неисправность зафиксирована.",
        "tg": "Носозӣ сабт шуд.",
        "uz": "Nosozlik qayd etildi.",
    },
    "required_photo_accepted": {
        "ru": "Принято: {label}",
        "tg": "Қабул шуд: {label}",
        "uz": "Qabul qilindi: {label}",
    },
    "required_photo_batch_progress": {
        "ru": "Принято: {label} ({received}/{total}). Осталось фото: {remaining}.",
        "tg": "Қабул шуд: {label} ({received}/{total}). Аксҳои боқимонда: {remaining}.",
        "uz": "Qabul qilindi: {label} ({received}/{total}). Qolgan foto: {remaining}.",
    },
    "required_photo_batch_done": {
        "ru": "Все 5 обязательных фото приняты ✅",
        "tg": "Ҳамаи 5 акси ҳатмӣ қабул шуд ✅",
        "uz": "Barcha 5 ta majburiy foto qabul qilindi ✅",
    },
    "required_photos_need_more_count": {
        "ru": "Не хватает еще фото: {remaining}. Отправьте недостающее количество.",
        "tg": "Ҳоло боз акс намерасад: {remaining}. Лутфан миқдори боқимондаро фиристед.",
        "uz": "Yana {remaining} ta foto yetishmayapti. Iltimos, qolganini yuboring.",
    },
    "required_photos_already_collected": {
        "ru": "Все 5 обязательных фото уже получены. Нажмите «Отправить отчет».",
        "tg": "Ҳамаи 5 акси ҳатмӣ аллакай қабул шудааст. «📤 Фиристодани ҳисобот»-ро пахш кунед.",
        "uz": "Barcha 5 ta majburiy foto allaqachon qabul qilingan. «📤 Hisobotni yuborish» ni bosing.",
    },
    "send_required_photos_batch_hint": {
        "ru": "Отправьте 5 обязательных фото одним сообщением (альбомом), затем отправьте геолокацию и нажмите «Отправить отчет».",
        "tg": "5 акси ҳатмиро якбора дар як паём (албом) фиристед, баъд геолокатсияро ирсол карда «📤 Фиристодани ҳисобот»-ро пахш кунед.",
        "uz": "5 ta majburiy fotoni bitta xabar (albom) qilib yuboring, so'ng geolokatsiyani yuborib «📤 Hisobotni yuborish» ni bosing.",
    },
    "photo_not_expected": {
        "ru": "Фото сейчас не ожидается. Следуйте шагам приемки.",
        "tg": "Ҳоло акс талаб намешавад. Қадамҳои қабулро идома диҳед.",
        "uz": "Hozircha foto kutilmayapti. Qabul bosqichlarini davom ettiring.",
    },
    "location_not_expected_yet": {
        "ru": "Геолокация пока не нужна. Сначала завершите чек-лист и отправьте 5 обязательных фото.",
        "tg": "Ҳоло геолокатсия лозим нест. Аввал чек-лист ва 5 акси ҳатмиро анҷом диҳед.",
        "uz": "Hozir geolokatsiya kerak emas. Avval chek-listni tugatib, 5 ta majburiy fotoni yuboring.",
    },
    "checklist_done_or_not_started": {
        "ru": "Чек-лист уже завершен или не начат.",
        "tg": "Чек-лист аллакай анҷом ёфтааст ё оғоз нашудааст.",
        "uz": "Chek-list allaqachon tugagan yoki boshlanmagan.",
    },
    "complete_nok_first": {
        "ru": "Сначала завершите текущий пункт «Не ОК» или отправьте «{back_text}».",
        "tg": "Аввал банди ҷории «На ОК»-ро анҷом диҳед ё «{back_text}»-ро фиристед.",
        "uz": "Avval joriy «OK emas» bandini yakunlang yoki «{back_text}» yuboring.",
    },
    "stale_button": {
        "ru": "Эта кнопка устарела. Используйте актуальный вопрос ниже.",
        "tg": "Ин тугма кӯҳна шудааст. Аз саволи ҷории поён истифода баред.",
        "uz": "Bu tugma eskirgan. Pastdagi joriy savoldan foydalaning.",
    },
    "invalid_button": {
        "ru": "Некорректная кнопка.",
        "tg": "Тугма нодуруст аст.",
        "uz": "Noto'g'ri tugma.",
    },
    "question_closed": {
        "ru": "Этот вопрос уже закрыт. Ответьте на текущий пункт ниже.",
        "tg": "Ин савол аллакай баста шудааст. Ба банди ҷории поён ҷавоб диҳед.",
        "uz": "Bu savol allaqachon yopilgan. Pastdagi joriy bandga javob bering.",
    },
    "already_first_question": {
        "ru": "Вы уже на первом пункте.",
        "tg": "Шумо аллакай дар банди аввал ҳастед.",
        "uz": "Siz allaqachon birinchi banddasiz.",
    },
    "cannot_undo": {
        "ru": "Не удалось отменить прошлый ответ.",
        "tg": "Ҷавоби қаблиро бекор кардан нашуд.",
        "uz": "Oldingi javobni bekor qilib bo'lmadi.",
    },
    "undo_saved": {
        "ru": "Последний ответ отменен",
        "tg": "Ҷавоби охирин бекор шуд",
        "uz": "Oxirgi javob bekor qilindi",
    },
    "returned_previous_question": {
        "ru": "Вернулись к прошлому вопросу. Ответьте заново.",
        "tg": "Ба саволи қаблӣ баргаштед. Аз нав ҷавоб диҳед.",
        "uz": "Oldingi savolga qaytdingiz. Qayta javob bering.",
    },
    "saved": {
        "ru": "Сохранено",
        "tg": "Сабт шуд",
        "uz": "Saqlandi",
    },
    "describe_issue_or_back": {
        "ru": "Опишите причину неисправности текстом.\nЕсли нажали «Не ОК» по ошибке, отправьте «{back_text}».",
        "tg": "Сабаби носозиро бо матн нависед.\nАгар «На ОК»-ро иштибоҳан пахш кардед, «{back_text}»-ро фиристед.",
        "uz": "Nosozlik sababini matn bilan yozing.\nAgar «OK emas» ni xato bosgan bo'lsangiz, «{back_text}» yuboring.",
    },
    "unknown_action": {
        "ru": "Неизвестное действие.",
        "tg": "Амали номаълум.",
        "uz": "Noma'lum amal.",
    },
    "use_commands_hint": {
        "ru": "Используйте /start — приёмка техники, /endday — завершение смены, /actions — действия в смене.",
        "tg": "Истифода баред: /start — қабули техника, /endday — анҷоми смена, /actions — амалҳои дар смена.",
        "uz": "Ishlatiling: /start — texnika qabul qilish, /endday — smenani tugatish, /actions — smenadagi harakatlar.",
    },
    "inspection_not_started": {
        "ru": "Приемка не начата.",
        "tg": "Қабул оғоз нашудааст.",
        "uz": "Qabul boshlanmagan.",
    },
    "missing_photos": {
        "ru": "Не хватает фото: {missing}",
        "tg": "Ин аксҳо намерасанд: {missing}",
        "uz": "Quyidagi fotolar yetishmayapti: {missing}",
    },
    "sending_report": {
        "ru": "Отправляю отчет",
        "tg": "Ҳисоботро мефиристам",
        "uz": "Hisobot yuborilmoqda",
    },
    "submit_report_button": {
        "ru": "📤 Отправить отчет",
        "tg": "📤 Фиристодани ҳисобот",
        "uz": "📤 Hisobotni yuborish",
    },
    "send_location_button": {
        "ru": "📍 Отправить геолокацию",
        "tg": "📍 Ирсоли геолокатсия",
        "uz": "📍 Geolokatsiyani yuborish",
    },
    "required_location_request": {
        "ru": "Теперь обязательно отправьте геолокацию кнопкой ниже.\nБез геолокации отчет не отправится.",
        "tg": "Акнун ҳатман геолокатсияро бо тугмаи поён ирсол кунед.\nБе геолокатсия ҳисобот фиристода намешавад.",
        "uz": "Endi geolokatsiyani pastdagi tugma orqali majburiy yuboring.\nGeolokatsiyasiz hisobot yuborilmaydi.",
    },
    "required_location_saved": {
        "ru": "Геолокация получена ✅",
        "tg": "Геолокатсия қабул шуд ✅",
        "uz": "Geolokatsiya qabul qilindi ✅",
    },
    "required_location_submit_hint": {
        "ru": "Нажмите «Отправить отчет». Геолокация будет включена в отчет.",
        "tg": "«📤 Фиристодани ҳисобот»-ро пахш кунед. Геолокатсия ба ҳисобот дохил мешавад.",
        "uz": "«📤 Hisobotni yuborish» ni bosing. Geolokatsiya hisobotga qo'shiladi.",
    },
    "required_location_missing": {
        "ru": "Сначала отправьте геолокацию после 5 фото.",
        "tg": "Аввал баъд аз 5 акс геолокатсияро фиристед.",
        "uz": "Avval 5 ta fotodan keyin geolokatsiyani yuboring.",
    },
    "submit_internal_error": {
        "ru": "Не удалось завершить отправку отчета из-за внутренней ошибки.\nПопробуйте еще раз позже или сообщите администратору.",
        "tg": "Фиристодани ҳисобот бинобар хатои дохилӣ анҷом нашуд.\nБаъдтар дубора кӯшиш кунед ё ба администратор хабар диҳед.",
        "uz": "Ichki xato sabab hisobot yuborilmadi.\nKeyinroq qayta urinib ko'ring yoki administratorga xabar bering.",
    },
    "send_required_photo": {
        "ru": "Пришлите: {label}",
        "tg": "Фиристед: {label}",
        "uz": "Yuboring: {label}",
    },
    "mechanic_only": {
        "ru": "Только механик/админ может принять решение.",
        "tg": "Фақат механик/админ метавонад қарор қабул кунад.",
        "uz": "Faqat mexanik/admin qaror qabul qila oladi.",
    },
    "report_not_found": {
        "ru": "Отчет не найден.",
        "tg": "Ҳисобот ёфт нашуд.",
        "uz": "Hisobot topilmadi.",
    },
    "decision_already_saved": {
        "ru": "Решение уже зафиксировано.",
        "tg": "Қарор аллакай сабт шудааст.",
        "uz": "Qaror allaqachon saqlangan.",
    },
    "decision_saved": {
        "ru": "Решение сохранено",
        "tg": "Қарор сабт шуд",
        "uz": "Qaror saqlandi",
    },
    "decision_by_mechanic": {
        "ru": "Решение по отчету #{inspection_id}: <b>{decision}</b> (механик: {mechanic_name})",
        "tg": "Қарор барои ҳисоботи #{inspection_id}: <b>{decision}</b> (механик: {mechanic_name})",
        "uz": "Hisobot #{inspection_id} bo'yicha qaror: <b>{decision}</b> (mexanik: {mechanic_name})",
    },
    "select_equipment_type": {
        "ru": "Выберите тип техники:",
        "tg": "Навъи техникаро интихоб кунед:",
        "uz": "Texnika turini tanlang:",
    },
    "select_equipment_brand": {
        "ru": "Выберите марку техники:",
        "tg": "Маркаи техникаро интихоб кунед:",
        "uz": "Texnika markasini tanlang:",
    },
    "select_equipment_number": {
        "ru": "Выберите номер техники:",
        "tg": "Рақами техникаро интихоб кунед:",
        "uz": "Texnika raqamini tanlang:",
    },
    "checklist_item": {
        "ru": "Пункт {current}/{total}:\n<b>{item}</b>",
        "tg": "Банд {current}/{total}:\n<b>{item}</b>",
        "uz": "Band {current}/{total}:\n<b>{item}</b>",
    },
    "required_photos_intro": {
        "ru": "Чек-лист завершен.\nТеперь обязательная фотофиксация:\n{photos}\nОтправьте сразу 5 фото одним сообщением (альбомом) в этом порядке.\nПосле 5 фото обязательно отправьте геолокацию.\nБез фото и геолокации отчет не отправится.",
        "tg": "Чек-лист анҷом ёфт.\nАкнун аксуратгирии ҳатмӣ:\n{photos}\nҲамаи 5 аксро якбора дар як паём (албом) бо ҳамин тартиб фиристед.\nБаъд аз 5 акс ҳатман геолокатсияро ирсол кунед.\nБе аксҳо ва геолокатсия ҳисобот фиристода намешавад.",
        "uz": "Chek-list tugadi.\nEndi majburiy fotofiksatsiya:\n{photos}\n5 ta fotoni shu tartibda bitta xabar (albom) qilib yuboring.\n5 ta fotodan keyin geolokatsiyani ham majburiy yuboring.\nFoto va geolokatsiyasiz hisobot yuborilmaydi.",
    },
    "inspection_not_started_use_start": {
        "ru": "Приемка не начата. Используйте /start.",
        "tg": "Қабул оғоз нашудааст. /start-ро истифода баред.",
        "uz": "Qabul boshlanmagan. /start dan foydalaning.",
    },
    "report_delivery_failed": {
        "ru": "Не удалось доставить отчет в чат механиков.\nПроверьте `MECHANIC_GROUP_ID` и что бот добавлен в группу, затем нажмите `Отправить отчет` снова.",
        "tg": "Ҳисоботро ба чати механикон фиристодан нашуд.\n`MECHANIC_GROUP_ID` ва илова будани бот ба гурӯҳро санҷед, баъд `Отправить отчет`-ро дубора пахш кунед.",
        "uz": "Hisobotni mexaniklar chatiga yuborib bo'lmadi.\n`MECHANIC_GROUP_ID` ni va bot guruhga qo'shilganini tekshiring, so'ng `Отправить отчет` ni qayta bosing.",
    },
    "report_delivered_with_missing_photos": {
        "ru": "Отчет №{inspection_id} доставлен механикам, но часть фото не отправилась ({photo_send_errors}).\nЭтап водителя завершен, механик получил карточку отчета.\nДля новой приемки используйте /start",
        "tg": "Ҳисоботи №{inspection_id} ба механикон расид, аммо қисми аксҳо фиристода нашуд ({photo_send_errors}).\nМарҳилаи ронанда анҷом ёфт, механик ҳисоботро гирифт.\nБарои қабули нав /start-ро истифода баред.",
        "uz": "Hisobot №{inspection_id} mexaniklarga yetkazildi, ammo ayrim fotolar yuborilmadi ({photo_send_errors}).\nHaydovchi bosqichi yakunlandi, mexanik hisobotni oldi.\nYangi qabul uchun /start dan foydalaning.",
    },
    "report_delivered_success": {
        "ru": "Отчет №{inspection_id} доставлен механикам. Этап водителя завершен.\nОжидайте решение механика.\nДля новой приемки используйте /start",
        "tg": "Ҳисоботи №{inspection_id} ба механикон расид. Марҳилаи ронанда анҷом ёфт.\nҚарори механикро интизор шавед.\nБарои қабули нав /start-ро истифода баред.",
        "uz": "Hisobot №{inspection_id} mexaniklarga yetkazildi. Haydovchi bosqichi yakunlandi.\nMexanik qarorini kuting.\nYangi qabul uchun /start dan foydalaning.",
    },
}


def normalize_language(language: str | None) -> str:
    if not language:
        return DEFAULT_LANGUAGE
    lowered = language.lower().strip()
    if lowered in SUPPORTED_LANGUAGES:
        return lowered
    return DEFAULT_LANGUAGE


def t(language: str | None, key: str, **kwargs: Any) -> str:
    lang = normalize_language(language)
    variants = TEXTS.get(key, {})
    template = variants.get(lang) or variants.get(DEFAULT_LANGUAGE) or key
    return template.format(**kwargs)


def back_label(language: str | None) -> str:
    return BACK_LABELS[normalize_language(language)]


def is_back_text(text: str) -> bool:
    normalized = text.strip().lower()
    return normalized in {value.lower() for value in BACK_LABELS.values()}


def required_photo_labels(language: str | None) -> dict[str, str]:
    return REQUIRED_PHOTO_LABELS_I18N[normalize_language(language)]


def checklist_items(
    language: str | None,
    driver_license_type: str | None = None,
    equipment_type: str | None = None,
) -> list[str]:
    lang = normalize_language(language)
    equipment_type_normalized = (equipment_type or "").strip()
    if equipment_type_normalized == DUMP_TRUCK_EQUIPMENT_TYPE:
        if (driver_license_type or "").strip().lower() == "foreign":
            return [*CHECKLIST_ITEMS_FOREIGN_I18N[lang], DUMP_TRUCK_TENT_ITEM_I18N[lang]]
        return [*CHECKLIST_ITEMS_I18N[lang], DUMP_TRUCK_TENT_ITEM_I18N[lang]]
    if equipment_type_normalized == "Катки":
        return CHECKLIST_ITEMS_ROLLERS_I18N[lang]
    if equipment_type_normalized in SPECIAL_CHECKLIST_WITHOUT_JOINTS_TYPES:
        return CHECKLIST_ITEMS_SPECIAL_WITHOUT_JOINTS_I18N[lang]
    if equipment_type_normalized in SPECIAL_CHECKLIST_EQUIPMENT_TYPES:
        return CHECKLIST_ITEMS_SPECIAL_I18N[lang]
    if (driver_license_type or "").strip().lower() == "foreign":
        return CHECKLIST_ITEMS_FOREIGN_I18N[lang]
    return CHECKLIST_ITEMS_I18N[lang]


def driver_license_type_labels(language: str | None) -> dict[str, str]:
    return DRIVER_LICENSE_TYPE_LABELS_I18N[normalize_language(language)]


def driver_license_type_display_map(language: str | None) -> dict[str, str]:
    labels = driver_license_type_labels(language)
    return {label: raw for raw, label in labels.items()}


def equipment_type_label(language: str | None, equipment_type: str) -> str:
    labels = EQUIPMENT_TYPE_LABELS_I18N[normalize_language(language)]
    return labels.get(equipment_type, equipment_type)


def equipment_type_display_map(language: str | None, equipment_types: list[str]) -> dict[str, str]:
    mapping: dict[str, str] = {}
    for item in equipment_types:
        localized = equipment_type_label(language, item)
        if localized in mapping and mapping[localized] != item:
            localized = f"{localized} ({item})"
        mapping[localized] = item
    return mapping


def daily_actions_display_map(language: str | None) -> dict[str, str]:
    return {
        t(language, "daily_action_blow_filters"): "blow_filters",
        t(language, "daily_action_workday_situations"): "workday_situations",
        t(language, "daily_action_refuel"): "refuel",
        t(language, "daily_action_end_workday"): "end_workday",
    }


def driver_status_text(language: str | None, decision: str) -> str:
    lang = normalize_language(language)
    variants = DRIVER_STATUS_TEXT_I18N.get(lang, DRIVER_STATUS_TEXT_I18N[DEFAULT_LANGUAGE])
    fallback = {
        "ru": "Решение по проверке принято.",
        "tg": "Қарор аз рӯи санҷиш қабул шуд.",
        "uz": "Tekshiruv bo'yicha qaror qabul qilindi.",
    }
    return variants.get(decision, fallback[lang])
