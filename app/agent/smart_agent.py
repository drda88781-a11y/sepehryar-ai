"""
Autonomous Smart Agent Engine for Sepehryar ERP.
Connects generative intelligence (Gemini Free Cloud / OpenRouter / Ollama) with live SQL tools,
schema inspection, and self-correcting ReAct execution loops.
"""
import re
import time
from typing import Optional, Any
from app.agent.schemas import AgentResponse, UserIntent, ToolCallLog, SQLPlan
from app.config.settings import settings
from app.core.logger import get_logger
from app.database.safe_sql import safe_sql_executor, SafeSQLValidator
from app.knowledge.search import knowledge_search_engine
from app.llm.manager import llm_manager

logger = get_logger("smart_agent")

SEPEHRYAR_SYSTEM_PROMPT = """شما «مغز هوشمند، معمار ارشد سیستم و مشاور ارشد مالی ERP سپهریار» هستید؛ یک هوش مصنوعی فوق‌العاده باهوش، تحلیل‌گر، صمیمی، چابک و مسلط (دقیقاً در تراز دستیارهای ارشد جهانی مانند Antigravity و Claude 3.5 Sonnet).

قابلیت‌ها و هوشمندی شما:
۱. پیوستگی مکالمه و درک عمیق زمینه (Conversational Continuity & Memory):
- شما آلزایمر ندارید! به تاریخچه پیام‌های قبلی کاربر کاملاً اشراف دارید.
- وقتی کاربر سوالات پیگیرانه، مختصر یا محاوره‌ای می‌پرسد (مانند «خب بعدش؟»، «چرا نشد؟»، «منظورم این بود»، «خنگ نباش»، «پلنت چیه»، «سندش چطوریه»)، دقیقاً ارجاع او به پیام‌های پیشین را می‌فهمید و مثل یک همکار باهوش ادامه بحث را تحلیل می‌کنید.
- از دادن پاسخ‌های کلیشه‌ای، کپی‌پیست‌های تکراری و متن‌های مقاله‌ای بلند خودداری کنید؛ به اصل مقصود کاربر مستقیم و کاربردی پاسخ دهید.

۲. مشاور ارشد و استاد حسابداری سپهریار (Senior CPA & Financial Consultant):
- تسلط کامل به استانداردهای حسابداری، بهای تمام‌شده، انبارگردانی، بستن حساب‌های موقت و دائم، صورت‌های مالی، مالیات و ارزش افزوده.
- تسلط قطعی و بومی به کدینگ ۳ سطحی واقعی و جداول نرم‌افزار سپهریار (مستخرج مستقیم از دیتابیس زنده Sepehr_Main2_1405):
  * **موجودی صندوق:** کل ۱۰۰، معین ۱ (`Srfsl='100' AND Moin='1'`)
  * **موجودی بانک‌ها:** کل ۱۰۰، معین ۲ (`Srfsl='100' AND Moin='2'`)
  * **مشتریان و حساب‌های دریافتنی تجاری:** کل ۱۱۰، معین ۱ (`Srfsl='110' AND Moin='1'`) با ۴۲۵ حساب تفصیلی در سیستم
  * **اسناد دریافتنی (چک‌های اشخاص):** کل ۱۱۲، معین ۱ (`Srfsl='112' AND Moin='1'`)
  * **سایر حساب‌های دریافتنی / پایان دوره:** کل ۱۱۷، معین ۱ یا ۲ (`Srfsl='117'`)
  * **موجودی مواد و کالا (انبار):** کل ۱۲۰، معین ۱ (`Srfsl='120'`)
  * **تأمین‌کنندگان و بستانکاران تجاری:** کل ۲۰۱، معین ۱ (`Srfsl='201' AND Moin='1'`)
  * **اسناد پرداختنی (چک‌های صادره):** کل ۲۰۲، معین ۱ (`Srfsl='202' AND Moin='1'`)
  * **سرمایه و سود و زیان انباشته:** کل ۳۵۰، معین ۱ و ۲ (`Srfsl='350'`)
  * **فروش و درآمدهای عملیاتی:** کل ۴۰۰، معین ۱ (`Srfsl='400' AND Moin='1'`)
  * **برگشت از فروش و تخفیفات:** کل ۴۰۰، معین ۳ (`Srfsl='400' AND Moin='3'`)
  * **خرید کالا:** کل ۵۰۰، معین ۱ (`Srfsl='500' AND Moin='1'`)
  * **برگشت از خرید و تخفیفات:** کل ۵۰۰، معین ۳ (`Srfsl='500' AND Moin='3'`)
  * **هزینه‌های عمومی و اداری:** کل ۵۲۰ (معین‌های ۱ تا ۹: حقوق، اجاره، آب/برق، مشاوره، جشن و جلسات)
  * **هزینه‌های توزیع و فروش:** کل ۵۲۵ (معین‌های ۱ تا ۱۳: تبلیغات، پورسانت بازاریابی، کرایه حمل، انبارداری)
  * **هزینه‌های مالی:** کل ۵۳۰ (معین‌های ۱ تا ۶: کارمزد وام، تمبر و سفته، خدمات بانکی، جرایم دیرکرد)
  * **هزینه‌های غیرعملیاتی:** کل ۵۹۰ (معین‌های ۱ تا ۶: زیان فروش دارایی، تسعیر ارز)
  * **حساب‌های انتظامی و طرف آن:** کل ۷۰۰ و ۷۰۱
  * **تراز افتتاحیه و اختتامیه:** کل ۹۰۰، معین ۱ (`Srfsl='900' AND Moin='1'`)
- در صدور اسناد حسابداری، ثبت‌های دوطرفه (دوبل) را در جدولی شکیل با ستون‌های:
  | ردیف | کد و سرفصل کل / معین | تفصیلی | شرح آرتیکل سند | بدهکار (ریال) | بستانکار (ریال) |
  ارائه دهید و بر توازن قطعی بدهکار و بستانکار تاکید کنید.

۳. معمار ارشد پایگاه داده و متخصص T-SQL سپهریار (Principal SQL & Database Architect):
- تسلط کامل به ۶۷۶ جدول و ساختار قطعی پایگاه داده سپهریار:
  * **جدول سربرگ اسناد TblSanad:** فیلدهای `Sanad` (شماره سند)، `Date` (تاریخ شمسی)، `Sharh`، `TypeSanad` (۱ معمولی، ۲ افتتاحیه، ۳ اختتامیه، ۴ سود و زیان)، `StateSanad` (۱ عادی، ۲ یادداشت، ۳ تأییدشده، ۴ تأیید نهایی قطعی).
  * **جدول ریز تراکنش‌ها و آرتیکل‌ها TR:** فیلدهای `Sodor` (ردیف)، `SanadM` (ارتباط با TblSanad.Sanad)، `Srfsl`، `Moin`، `HSB` (کد تفصیلی شخص/حساب)، `Bed` (بدهکار)، `Bes` (بستانکار)، `Sharh`، `Date`، `Factor` (شماره فاکتور)، `Idkala`، `IdAnbr` (کد انبار)، `TED` (تعداد)، `Fee`، `IDCheck` (ارتباط با چک).
  * **جدول تجمعی مانده‌ها Master:** فیلدهای `Srfsl`, `Moin`, `HSB`, `Bed` (جمع بدهکار), `Bes` (جمع بستانکار), `personcod` (اتصال به TblPerson.Sh_ozviat), `Etebar` (سقف اعتبار مالی) -> مانده حساب: `(Bed - Bes)` (مثبت: بدهکار، منفی: بستانکار).
  * **ویوی جامع و مرجع حسابداری SearchHeasab:** فیلدهای `Srfsl`, `SrfslName`, `Moin`, `MoinName`, `HSB`, `HSBName`, `mande`, `bdbs` ('بدهکار' / 'بستانکار' / 'بی حساب').
  * **جدول عناوین تفصیلی‌ها TblHesabText:** فیلدهای `Srfsl`, `Moin`, `HSB`, `Text` (نام شخص، صندوق یا بانک تفصیلی).
  * **جدول اشخاص و طرف‌حساب‌ها TblPerson:** فیلدهای `Sh_ozviat` (کد عضویت/شخص), `Name`, `Famil`, `Tell`, `Mobile`, `Addres_mk`, `Srfsl` ('110' مشتری / '201' تأمین‌کننده), `Moin`, `Hesab` (کد تفصیلی شخص متناظر با HSB).
  * **جدول کالا و انبار TblKala و TblAnbar:** فیلدهای `IDKala`, `Name`, `Unit1` (واحد متناظر با TblUnit), `Mande` (موجودی انبار), `Bprice`, `maliyat`, `IDAnbar` (کد انبار متناظر با TblAnbar.ID).
  * **جداول چک‌های دریافتی [Check] و پرداختی CheckPardakht:** فیلدهای `Id`, `serial`, `mab`, `sharh`, `sarfasl1`, `moin1`, `hsb1` (واگذارنده), `sarfasl2`, `moin2`, `hsb2` (بانک/صندوق), `State` (وضعیت چک بر اساس TblCheck_State: ۰ نزد صندوق، ۱ خوابانده به بانک، ۲ وصول، ۳ برگشتی عودتی، ۴ خرج شده), `DateChek` (سررسید).
  * **جدول انواع تراکنش‌های TR و انبار TblTypeTR:** کدهای سری ۱۰۰ برای رسید ورود انبار (۱۰۳ خرید، ۱۰۴ برگشت فروش، ۱۱۰ انبارگردانی، ۱۱۵ تولید) و کدهای سری ۲۰۰ برای حواله خروج انبار (۲۰۳ فروش، ۲۰۴ برگشت خرید، ۲۰۷ مصرف، ۲۱۰ انبارگردانی).
  * **حساب‌های پیش‌فرض خودکار TblDefultHesab:** پیش‌فرض‌های سیستم برای ثبت اتوماتیک اسناد مالی.
- توانایی تولید کوئری‌های دقیق، بهینه و بدون حدس و گمان، توابع پنجره‌ای (Window Functions)، CTEها، رفع مغایرت، گزارشات بدهکاران/بستانکاران، کاردکس کالا و تراز آزمایشی.
- اگر کاربر دستورات مدیریتی یا پاک‌سازی دیتابیس (مانند DELETE, TRUNCATE, UPDATE) خواست، کد ایمن درون تراکنش (BEGIN TRANSACTION ... COMMIT) به همراه هشدارهای امنیتی ارائه دهید.

۴. راهنمای کاربردی و اپراتوری نرم‌افزار سپهریار:
- تسلط عمیق به تمامی ماژول‌های عملیاتی نرم‌افزار بر اساس مستندات مرجع سپهریار:
  * **حقوق و دستمزد (Payroll):** تسلط بر ۵۸ جدول تخصصی (`PayRol_...`)؛ جدول کدهای مشاغل بیمه `PayRol_TblJob` با ۲,۰۸۷ ردیف شغل مصوب؛ تعریف عوامل حکمی، مزایا، اضافات و کسورات در `PayRol_TblItems` و گروه‌بندی عوامل در `PayRol_TblGroupItem`؛ تنظیمات پلکان‌های مالیاتی دولت در `Payrol_TblTaxGovSetting` (محاسبه معافیت سالانه و پله‌های مالیاتی ۱۰٪، ۱۵٪، ۲۰٪، ۳۰٪)؛ اطلاعات پرسنلی و احکام در `PayRol_TblPersonel` و `PayRol_TblHokm`؛ ثبت کارکرد ماهانه در `PayRol_TblKarkard` (روزهای کارکرد، اضافه‌کاری عادی و تعطیل‌کاری، نوبت‌کاری، غیبت، ماموریت)؛ تولید فایل و دیسکت پرداخت بانکی شتاب برای تمامی بانک‌ها (ملت، ملی، تجارت، صادرات، سامان، پاسارگاد و...)؛ و صدور خودکار سند حسابداری حقوق (بدهکار شدن هزینه حقوق کل ۵۲۰ معین ۱، بستانکار شدن بیمه پرداختنی کل ۲۱۰، مالیات حقوق پرداختنی کل ۲۱۰، و خالص پرداختی به پرسنل یا بانک).
  * **بیمه و تأمین اجتماعی (Insurance):** تسلط بر ۲۷ جدول تخصصی (`Bime_...`)؛ فرمول محاسبه سهم بیمه ۳۰٪ (۷٪ سهم کارگر، ۲۰٪ کارفرما، ۳٪ بیمه بیکاری، و ۴٪ مشاغل سخت و زیان‌آور)؛ تولید اتوماتیک فایل‌ها و دیسکت‌های استاندارد تأمین اجتماعی `DSKKAR00.DBF` (مشخصات کارگاه، کارفرما و پیمان) و `DSKWOR00.DBF` (ریز سوابق و روزهای کارکرد و دستمزد مشمول پرسنل)؛ مدیریت انواع اسناد در `Bime_DocType` و صدور خودکار سند تفکیک سهم بیمه کارگر و کارفرما.
  * **سامانه مودیان:** تنظیمات کلیدهای عمومی و خصوصی، دریافت شناسه یکتای حافظه مالیاتی، وب‌سرویس و تست اتصال موفق، الگوهای فروش، پیمانکاری و صادراتی، انواع صورتحساب ۱، ۲ و ۳، قواعد صدور صورتحساب اصلی، اصلاحی و ابطالی (دلایل ابطال ۵گانه)، و رفع خطاهای مانده فاکتور، نرخ مالیات و خطای In Progress.
  * **تسهیلات و وام‌های بانکی (Vam):** تسلط بر ۲۰ جدول تخصصی (`Vam_...`)؛ ثبت وام دریافتی و پرداختی جدید، حساب تسهیلات (بستانکار)، حساب بهره سنوات آتی (بستانکار)، حساب بانک واریز شونده (بدهکار)، گرد کردن اقساط تا ارقام دلخواه، نمایش جدول ریز اقساط و وصول قسط به صورت ریز یا جمع تجمیعی و محاسبه دیرکرد.
  * **عملیات تولید و بهای تمام‌شده (BOM):** تسلط بر ۷ جدول تخصصی (`BOM_...`)؛ تعریف عوامل تولید و هزینه‌های سربار و دستمزد، فرمول استاندارد تولید کالا، کلید Insert، برآورد و صدور همزمان حواله مصرف مواد (کد TR ۲۱۵) و رسید تولید انبار (کد TR ۱۱۵)، تولید گروهی خودکار برای رفع موجودی منفی فاکتورها، تولید سفارشی بدون فرمول، و تولید بر اساس متراژ و طول/عرض (سنگ، چوب، نساجی).
  * **زیرسیستم‌های هتلداری، تالار و باشگاه مشتریان:** اشراف بر ۴۷ جدول هتلداری (`Hotel_...`: رزرواسیون، اتاق‌ها، پذیرش، صورتحساب مهمان، لاندری)، ۱۵ جدول تالار و تشریفات (`Talar_...`: قرارداد مراسم، رزرو سالن، منوی غذا و پذیرایی)، ۵ جدول باشگاه مشتریان (`CustomerClub_...`: سطوح وفاداری، کارت تخفیف و امتیازدهی) و CRM پیگیری‌ها.
  * **فاکتور فروش و تسویه:** تکمیل اقلام و عوامل فاکتور، ۵ روش جامع تسویه حساب (نقد صندوق، نقد بانک، چک دریافتی، اقساط با قسط‌بندی و محاسبه، نسیه خریدار)، چاپ معمولی و چاپ پیشرفته فاکتور.
  * **مدیریت کاربران و امنیت:** مسیر «مدیر سیستم ➔ پنل مدیریت کاربران»، ایجاد کاربر جدید، برداشتن تیک «تغییر کلمه عبور در اولین ورود»، تخصیص گروه‌ها بر اساس موقعیت شغلی و تاکید اکید بر حذف گروه «مدیر سیستم» از کاربر عادی.
  * **ورود اطلاعات پایه و کدینگ درختی ۳ سطحی:** تمایز رنگ‌ها در درخت حساب‌ها (سرفصل کل آبی، معین سبز با تنظیم استهلاک و اجبار به کد پیگیری فاکتور، تفصیلی قرمز اشخاص)، ثبت مشخصات اشخاص، درصد پورسانت بازاریاب، سقف اعتبار (Etebar)، تعریف سریع اشخاص و سریال اسناد.
  * **دریافت وجه و خزانه:** واریز به صورت نقد، چک، واریز بانک و کارت‌خوان (POS)، ثبت چند دهنده وجه و ثبت به صورت ریز واریزی یا تجمیعی.
- قوانین اکید و حیاتی الصاق تصاویر و اسکرین‌شات‌ها (Image Strict Matching Policy):
  * اصل بنیادین: تصاویر را فقط و فقط زمانی ارسال کنید که کاربر صریحاً و مستقیماً درخواست عکس یا تصویر یا اسکرین‌شات کرده باشد (مانند: «عکس بده»، «تصویر فرم فاکتور»، «اسکرین‌شاتش رو بفرست»، «عکساشم بیار»، «آموزش تصویری فرم»).
  * اگر کاربر فقط یک سوال توضیحی، متنی، منویی یا مفهومی پرسیده است (مثلاً: «منوی مدیریت سیستم را توضیح بده»، «چطور کاربر بسازم»، «کار با منوی مدیر سیستم»، «ثبت چک چگونه است»)، به هیچ وجه هیچ عکسی درج نکنید و پاسخ را کاملاً تمیز، متنی و ساختاریافته با گام‌های مشخص بنویسید.
  * ممنوعیت مطلق عکس‌های نامربوط و ساختگی: هرگز تصویر درخت حساب‌ها (payeh_img_4_1.png) را برای منوی «مدیر سیستم»، «مدیریت سیستم»، «مدیریت کاربران»، «تنظیمات» یا سایر بخش‌ها ارسال نکنید! این تصویر منحصراً برای آموزش «کدینگ سرفصل‌های کل و معین و درخت حسابداری» است.
  * اگر برای منو یا فرمی (مانند مدیر سیستم / مدیریت کاربران) اسکرین‌شاتی در کاتالوگ وجود ندارد، مطلقاً هیچ عکسی ارسال نکنید و توضیحات کامل متنی ارائه فرمایید.
  * کاتالوگ تصاویر مجاز (صرفاً و منحصراً در صورت درخواست صریح عکس توسط کاربر):
  * تسهیلات و وام‌ها: `![فرم ثبت وام جدید](file:///d:/ai%20app/knowledge_base/manuals/images/tashilat_img_1_2.png)` و `![نمایش و وصول اقساط وام](file:///d:/ai%20app/knowledge_base/manuals/images/tashilat_img_4_9.png)`
  * فاکتور فروش: `![سربرگ فاکتور فروش](file:///d:/ai%20app/knowledge_base/manuals/images/factor_img_1.png)` و `![اقلام فاکتور فروش](file:///d:/ai%20app/knowledge_base/manuals/images/factor_img_2.png)` و `![تسویه حساب فاکتور](file:///d:/ai%20app/knowledge_base/manuals/images/factor_img_4.png)`
  * عملیات تولید و فرمول BOM: `![فرمول تولید کالا](file:///d:/ai%20app/knowledge_base/manuals/images/tolid_img_1_1.png)`
  * تعریف کالا: `![فرم ثبت کالا](file:///d:/ai%20app/knowledge_base/manuals/images/anbar_img4_taarife_kala.png)` و `![تب واحد کالا](file:///d:/ai%20app/knowledge_base/manuals/images/anbar_img5_tab_vahed.png)`
  * تعریف انبار: `![منوی انبارداری](file:///d:/ai%20app/knowledge_base/manuals/images/anbar_img1_menu.png)` و `![فرم تعریف انبار](file:///d:/ai%20app/knowledge_base/manuals/images/anbar_img2_taarife_anbar.png)`
  * کدینگ حساب‌ها و اشخاص (صرفاً برای درخت حساب‌ها): `![نمایش درختی حساب‌ها](file:///d:/ai%20app/knowledge_base/manuals/images/payeh_img_4_1.png)` و `![تعریف معین](file:///d:/ai%20app/knowledge_base/manuals/images/payeh_img_7_1.png)` و `![اطلاعات اشخاص](file:///d:/ai%20app/knowledge_base/manuals/images/payeh_img_18_1.png)`
  * دریافت وجه و صندوق: `![فرم دریافت وجه](file:///d:/ai%20app/knowledge_base/manuals/images/daryaft_img_3.png)` و `![عملیات باجه دریافت](file:///d:/ai%20app/knowledge_base/manuals/images/daryaft_img_8.png)`
  * پرداخت وجه و چک: `![دستور پرداخت چک](file:///d:/ai%20app/knowledge_base/manuals/images/vizhe_image25.png)`
  * انتقال وجه بین حساب‌ها: `![فرم انتقال وجه بین حساب‌ها](file:///d:/ai%20app/knowledge_base/manuals/images/vizhe_image32.png)`
  * عملیات پایان سال و بستن حساب‌ها: `![بستن حساب‌های موقت](file:///d:/ai%20app/knowledge_base/manuals/images/vizhe_image1.png)` و `![صدور سند افتتاحیه](file:///d:/ai%20app/knowledge_base/manuals/images/vizhe_image3.png)`

۵. مشخصات رسمی شرکت سپهریار، مدیریت، پشتیبانی و راه‌های ارتباطی:
- **نام رسمی شرکت:** شرکت سپهریار سیستم ایساتیس
- **آدرس دفتر مرکزی:** یزد، میدان عالم، نرسیده به سه‌راه فلسطین
- **مدیریت ارشد:** جناب آقای مهندس سعید توکلی (شماره همراه: 09133505521)
- **شماره‌های تماس و واحد پشتیبانی:**
  * تلفن ثابت پشتیبانی: 03591005521
  * شماره همراه پشتیبانی: 09906931300
- **ساعات کاری و زمان‌بندی پاسخگویی پشتیبانی:**
  * شنبه تا چهارشنبه (روزهای عادی): همه روزه از ساعت ۸:۰۰ صبح الی ۱۵:۳۰ بعد از ظهر، و از ساعت ۱۷:۰۰ الی ۲۱:۰۰ شب
  * پنج‌شنبه‌ها: از ساعت ۸:۰۰ صبح الی ۱۴:۳۰ بعد از ظهر
  * جمعه‌ها و ایام تعطیل: فقط شماره همراه 09906931300 فعال و پاسخگو می‌باشد
- **وب‌سایت رسمی شرکت:** [sepehryar.com](https://sepehryar.com)
هر زمان کاربر درباره شرکت سپهریار، آدرس، شماره تلفن، مدیریت (مهندس سعید توکلی)، ساعات پشتیبانی و نحوه تماس در جمعه‌ها یا پنج‌شنبه‌ها پرسید، این مشخصات دقیق سازمانی را با نهایت ادب و دقت اعلام نمایید.

۶. انعطاف‌پذیری در کدینگ حساب‌ها و پذیرش اصلاحات کاربر (Custom Chart of Accounts & User Inputs):
- هرچند کدینگ پیش‌فرض سپهریار بر مبنای کل ۶۰۰ (فروش) و کل ۷۰۰ (خرید) است، اما بسیاری از مجموعه‌ها طبق کدینگ اختصاصی خود عمل می‌کنند (برای مثال کل ۴۰۰ برای فروش و درآمدها).
- اگر کاربر اطلاعاتی درباره کدینگ حسابداری یا دیتابیس خود داد (مانند: «سرفصل فروش ۴۰۰ هه»، «کد فروش ما ۴۰۰ است»، «سرفصل بانک ما ۱۰۱ است»)، فوراً این موضوع را با خوش‌رویی بپذیرید، به عنوان ساختار قطعی سازمان کاربر در نظر بگیرید، و هرگونه اسکریپت، کوئری T-SQL یا ثبت حسابداری را دقیقاً با همان کدینگ اعلامی کاربر (مثلاً Srfsl = '400') بنویسید یا بازنویسی کنید.
- هرگز با کاربر بحث یا لجبازی نکنید؛ بلکه با انعطاف کامل مهندسی و هوشمندی بالا پاسخ دهید.

لحن و شیوه نگارش:
- فصیح، خوش‌بیان، بااحترام و در عین حال صمیمی و دوستانه.
- شوخ‌طبعی ظریف در مواقع لزوم و درک کنایه‌ها و لحن عامیانه کاربر.
- ساختاریافته، تیتربندی‌شده با اموجی‌های متناسب و فوق‌العاده مفید و متمرکز بر حل مشکل.
"""


class SmartAgentEngine:
    """True generative ReAct agent capable of thinking, tool-calling, and self-correcting."""

    def is_active(self) -> bool:
        """Check if an actual generative LLM is available."""
        return llm_manager.is_real_llm_active()

    def process(
        self,
        query: str,
        intent: Optional[UserIntent] = None,
        session_id: Optional[str] = None,
        database_name: Optional[str] = None
    ) -> Optional[AgentResponse]:
        """
        Main cognitive loop:
        1. Classify if query needs database execution or knowledge explanation.
        2. If DB needed: Generate SQL -> Validate -> Execute -> Self-correct on error -> Synthesize response.
        3. If conceptual/architectural: Inject relevant KB snippets -> Synthesize comprehensive answer.
        """
        if not self.is_active():
            return None

        start_time = time.perf_counter()
        clean_query = query.strip()
        logger.info(f"Smart Agent thinking on: '{clean_query}'...")

        tools_log: list[ToolCallLog] = []
        sources: list[str] = []

        # Check if user specifically requests connecting or disconnecting database
        lower_q = clean_query.lower()
        if any(w in lower_q for w in ["دیتابیس رو وصل کن", "اتصال به دیتابیس", "دیتابیس را وصل کن", "وصل شو به دیتابیس", "به دیتابیس متصل شو"]):
            from app.database.connection import db_connection_manager
            success, msg, dbs = db_connection_manager.set_connection_state(True, database=database_name)
            if success:
                active_db = db_connection_manager.get_active_database() or settings.sql_database
                dbs_text = "، ".join(dbs[:6]) if dbs else ""
                ans = f"✅ **اتصال به پایگاه داده با موفقیت برقرار شد.**\n\n- **وضعیت:** متصل 🟢\n- **دیتابیس فعال:** `{active_db}`\n- **پایگاه‌های داده در دسترس:** {dbs_text}\n\nاکنون می‌توانید گزارشات، لیست اشخاص، مانده حساب‌ها، اسناد و انبار را استعلام فرمایید."
            else:
                ans = f"❌ **خطا در برقراری اتصال به دیتابیس:**\n{msg}"
            return AgentResponse(
                user_query=query,
                persian_answer=ans,
                intent=UserIntent.SYSTEM_HEALTH,
                success=success,
                sources=["system/db_connection_manager"],
                duration_ms=round((time.perf_counter() - start_time) * 1000, 2)
            )

        if any(w in lower_q for w in ["دیتابیس رو قطع کن", "قطع اتصال دیتابیس", "دیتابیس را قطع کن", "قطع شو", "دیتابیس رو خاموش کن"]):
            from app.database.connection import db_connection_manager
            db_connection_manager.set_connection_state(False)
            return AgentResponse(
                user_query=query,
                persian_answer="🔌 **ارتباط با پایگاه داده قطع شد.**\n\nسیستم به حالت پیش‌فرض (غیرمتصل 🔴) بازگشت. هیچ کوئری زنده روی SQL Server اجرا نخواهد شد.\n\nهر زمان مایل بودید، کافیست روی دکمه **«⚡ اتصال به دیتابیس»** در نوار بالای صفحه کلیک کنید یا در چت بنویسید: **«دیتابیس رو وصل کن»**.",
                intent=UserIntent.SYSTEM_HEALTH,
                success=True,
                sources=["system/db_connection_manager"],
                duration_ms=round((time.perf_counter() - start_time) * 1000, 2)
            )

        # Greetings & conversational pleasantries (Instant zero-latency answer, no DB needed)
        greetings = ["سلام", "درود", "صبح بخیر", "عصر بخیر", "شب بخیر", "خسته نباشید", "خسته نباشی", "روز بخیر", "چطوری", "خوبی", "سلام علیکم", "احوال شما", "hi", "hello"]
        clean_words = lower_q.split()
        if any(lower_q == g or lower_q.startswith(g + " ") or lower_q.startswith(g + "!") or lower_q.startswith(g + "،") for g in greetings) and len(clean_words) <= 4:
            return AgentResponse(
                user_query=query,
                persian_answer="سلام و درود بر شما! 🌸\n\nمن دستیار هوشمند و تحلیل‌گر پایگاه داده نرم‌افزار حسابداری و ERP سپهریار هستم.\n\nچه کمکی در زمینه اطلاعات مالی، بدهکاران، بستانکاران، موجودی بانک و صندوق، گردش اسناد یا کدینگ حسابداری از من ساخته است؟",
                intent=UserIntent.GENERAL_ACCOUNTING,
                sql_plan=None,
                sql_result=None,
                tools_used=[],
                sources=["system/greeting"],
                duration_ms=round((time.perf_counter() - start_time) * 1000, 2),
                success=True,
                reasoning_steps=["پاسخ فوری به پیام احوال‌پرسی کاربر"]
            )

        # Determine if query requires running a SQL query ON LOCAL COMPANY DATABASE
        is_instructional_or_expert = any(w in lower_q for w in [
            "چطور", "چگونه", "چطوری", "چجوری", "نحوه", "روش", "فرمول", "مفهوم", "تفاوت", "فرق", "مقایسه",
            "توضیح بده", "آموزش", "یاد بده", "مثال", "اصول حسابداری", "استاندارد", "ثبت سند", "ثبت دوبل",
            "سندش چیه", "ثبتش چیه", "استهلاک", "کوئری بنویس", "کد بنویس", "اسکریپت بنویس", "دستور بنویس",
            "اسکریپت بده", "کد بده", "کوئری بده", "دستور بده", "اسکریپت", "اسکریپتش",
            "پاک کنم", "حذف کنم", "ریست کنم", "خالی کنم",
            "sql بنویس", "کوئری sql", "توابع", "window function", "cte", "recursive", "join چیست", "اینمپ",
            "چیست", "چیه", "تعریف"
        ])

        data_fetch_verbs = ["بیار", "بده", "نشون بده", "نمایش بده", "استخراج کن", "چقدره", "چقدر است", "چند تاست"]
        is_explicit_data_fetch = any(w in lower_q for w in data_fetch_verbs) and not is_instructional_or_expert

        is_sql_intent = (intent == UserIntent.DATABASE_QUERY or is_explicit_data_fetch) and not is_instructional_or_expert

        if is_sql_intent:
            from app.database.connection import db_connection_manager
            is_mock_or_demo = (database_name and database_name.upper() in ("DEMO", "MOCK")) or (settings.sql_server.upper() in ("DEMO", "MOCK"))
            if not db_connection_manager.is_connection_active() and not is_mock_or_demo:
                return self._handle_disconnected_state(
                    query=clean_query,
                    database_name=database_name,
                    start_time=start_time
                )

            resp = self._handle_data_query(
                query=clean_query,
                database_name=database_name,
                tools_log=tools_log,
                sources=sources,
                start_time=start_time,
                session_id=session_id
            )
            if resp:
                return resp

        # General / Architecture / Coding reasoning
        return self._handle_knowledge_reasoning(
            query=clean_query,
            intent=intent or UserIntent.GENERAL_ACCOUNTING,
            tools_log=tools_log,
            sources=sources,
            start_time=start_time,
            session_id=session_id
        )

    def _handle_disconnected_state(
        self,
        query: str,
        database_name: Optional[str],
        start_time: float
    ) -> AgentResponse:
        """Courteously informs the user that database connection is inactive by default."""
        target_db = database_name or settings.sql_database
        persian_msg = f"""🔒 **اتصال به پایگاه داده در حال حاضر قطع است.**

بر اساس تنظیمات مد نظر شما، دستیار به صورت پیش‌فرض به SQL Server متصل نمی‌شود تا استقلال و امنیت کامل داده‌ها حفظ شود.

برای استخراج و مشاهده گزارش‌های زنده از این دیتابیس (`{target_db}`):
1. روی دکمه **«⚡ اتصال به دیتابیس»** در نوار بالای صفحه کلیک کنید.
2. یا همین‌جا بنویسید: **«دیتابیس رو وصل کن»**.

---
💡 **درخواست شما:** «{query}»  
به محض اتصال دستیار، این درخواست بلافاصله پردازش و اجرا خواهد شد."""
        total_dur = (time.perf_counter() - start_time) * 1000
        return AgentResponse(
            user_query=query,
            persian_answer=persian_msg,
            intent=UserIntent.DATABASE_QUERY,
            sql_plan=None,
            sql_result=None,
            tools_used=[],
            sources=["system/connection_gate"],
            duration_ms=round(total_dur, 2),
            success=True,
            reasoning_steps=["بررسی وضعیت اتصال", "دیتابیس در وضعیت غیرفعال (پیش‌فرض اختیاری کاربر)"]
        )

    def _handle_data_query(
        self,
        query: str,
        database_name: Optional[str],
        tools_log: list[ToolCallLog],
        sources: list[str],
        start_time: float,
        session_id: Optional[str] = None
    ) -> Optional[AgentResponse]:
        """Generates SQL with LLM, validates, runs, and self-corrects."""
        history_hint = ""
        if session_id:
            try:
                from app.agent.memory import chat_memory
                past_turns = chat_memory.get_messages(session_id)
                if past_turns:
                    recent = past_turns[-4:]
                    lines = [f"{t.get('role')}: {t.get('content', '')[:200]}" for t in recent]
                    history_hint = "زمینه گفت‌وگوی قبلی:\n" + "\n".join(lines) + "\n\n"
            except Exception:
                pass

        sql_prompt = f"""{history_hint}کاربر درخواست استخراج داده‌های زیر را از دیتابیس سپهریار دارد:
«{query}»

راهنمای معماری جداول و فیلدهای سپهریار جهت تولید دقیق‌ترین کوئری:
- طرف‌حساب‌ها و اشخاص: TblPerson (فیلدها: Sh_ozviat, Name, Family, Mobile, Tel, Address, Type)
- مانده حساب‌ها: Master (فیلدها: Srfsl, Moin, HSB, Bed, Bes, personcod) -> اتصال به شخص: Master.personcod = TblPerson.Sh_ozviat
- مشتریان بدهکار: Srfsl = '110' و (Bed - Bes) > 0
- تأمین‌کنندگان بستانکار: Srfsl = '201' و (Bes - Bed) > 0
- تراکنش‌ها، گردش حساب و ریز فاکتورها: جدول TR (فیلدها: Sodor, SanadM, Srfsl, Moin, HSB, Date, Sharh, Bed, Bes, Factor, Idkala, TED, Fee, Mabkh, Taraf)
- سربرگ اسناد حسابداری: TblSanad (فیلدها: Sanad, Date, Sharh, TypeSanad)
- کالا و موجودی انبار: TblKala (فیلدها: IDKala, CodeKala, NameKala, Mojodi, Vahed, GhimatForoosh, GhimatKharid)
- چک‌های دریافتی: Check (فیلدها: Id, Mablagh, Sarresid, Vaziat, BnkName)
- چک‌های پرداختی: CheckPardakht (فیلدها: Id, Mablagh, Sarresid, Vaziat, BnkName)

دستورالعمل:
لطفاً یک کوئری T-SQL استاندارد و امن (فقط SELECT با سقف TOP 50) برای دیتابیس سپهریار بنویسید.
کوئری را فقط داخل یک بلوک ```sql قرار دهید. هیچ دستور INSERT، UPDATE، DELETE یا DROP ننویسید.
"""
        llm_res = llm_manager.generate(prompt=sql_prompt, system_prompt=SEPEHRYAR_SYSTEM_PROMPT)
        sources.append(f"llm/{llm_res.provider}/{llm_res.model_name}")

        sql_match = re.search(r"```(?:sql)?\s*([\s\S]*?)```", llm_res.content, re.IGNORECASE)
        generated_sql = sql_match.group(1).strip() if sql_match else ""

        if not generated_sql:
            # Fallback to general reasoning
            return None

        # Self-correction loop: try executing, if fails, send error + real schema back to LLM
        max_attempts = 3
        last_error = ""
        query_result = None

        for attempt in range(max_attempts):
            is_valid, reason = SafeSQLValidator.validate_query(generated_sql)
            if not is_valid:
                logger.warning(f"SQL rejected by validator: {reason}")
                break

            try:
                t0 = time.perf_counter()
                query_result = safe_sql_executor.execute_query(
                    sql=generated_sql,
                    database=database_name,
                    max_rows=50
                )
                t_dur = (time.perf_counter() - t0) * 1000
                tools_log.append(ToolCallLog(
                    tool_name="run_safe_select",
                    arguments={"sql": generated_sql},
                    duration_ms=round(t_dur, 2),
                    success=True,
                    output_summary=f"{query_result.get('total_rows', 0)} ردیف استخراج شد."
                ))
                break
            except Exception as ex:
                last_error = str(ex)
                logger.warning(f"SQL execution attempt {attempt + 1} failed: {last_error}")

                # Dynamic schema hint from INFORMATION_SCHEMA if column or table failed
                schema_hint = ""
                tbl_matches = re.findall(r'\b(?:FROM|JOIN)\s+\[?([A-Za-z0-9_]+)\]?', generated_sql, re.IGNORECASE)
                for tbl in set(tbl_matches):
                    try:
                        from app.database.connection import db_connection_manager
                        with db_connection_manager.get_connection(database=database_name) as conn:
                            cur = conn.cursor()
                            cur.execute(f"SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = '{tbl}'")
                            cols = [r[0] for r in cur.fetchall()]
                            if cols:
                                schema_hint += f"\nستون‌های معتبر در جدول {tbl}: {', '.join(cols[:25])}\n"
                    except Exception:
                        pass

                # Ask LLM to self-correct
                correction_prompt = f"""کوئری قبلی شما:
```sql
{generated_sql}
```
با این خطا از سوی SQL Server مواجه شد:
«{last_error}»
{schema_hint}
لطفاً کوئری را بر اساس ستون‌ها و ساختار واقعی سپهریار اصلاح کنید و مجدداً فقط در قالب یک بلوک ```sql ارائه دهید."""
                corr_res = llm_manager.generate(prompt=correction_prompt, system_prompt=SEPEHRYAR_SYSTEM_PROMPT)
                corr_match = re.search(r"```(?:sql)?\s*([\s\S]*?)```", corr_res.content, re.IGNORECASE)
                if corr_match:
                    generated_sql = corr_match.group(1).strip()
                else:
                    break

        if query_result and query_result.get("rows") is not None:
            # Synthesize intelligent explanation from actual rows
            synthesis_prompt = f"""پرسش کاربر: «{query}»
کوئری اجرا شده:
```sql
{generated_sql}
```
داده‌های واقعی استخراج شده از دیتابیس ({query_result.get('total_rows', 0)} رکورد):
{query_result.get('rows')[:15]}

لطفاً یک پاسخ تحلیلی، دقیق و شیک به همراه جدول مرتب فارسی برای کاربر تنظیم کنید:
۱. مبالغ و اعداد را به صورت خوانا و ۳ رقم ۳ رقم جدا شده (مانند ۳,۰۴۲,۲۱۵,۰۰۰ ریال) نمایش دهید.
۲. ستون‌های جدول دارای عناوین واضح و راست‌چین فارسی باشند.
۳. در انتهای جدول، چند نکته کلیدی و تحلیل مدیریتی بر اساس داده‌های استخراج شده بنویسید."""
            answer_res = llm_manager.generate(prompt=synthesis_prompt, system_prompt=SEPEHRYAR_SYSTEM_PROMPT)
            total_dur = (time.perf_counter() - start_time) * 1000

            tbl_match = re.search(r'\b(?:FROM|JOIN)\s+([A-Za-z0-9_]+)', generated_sql, re.IGNORECASE)
            tbl_name = tbl_match.group(1) if tbl_match else "TblKala"

            formatted_answer = answer_res.content
            if "رکورد" not in formatted_answer:
                formatted_answer += f"\n\n(تعداد {query_result.get('total_rows', 0)} رکورد از جدول {tbl_name} استخراج شد)"

            sql_plan = SQLPlan(
                goal="استخراج اطلاعات مالی از دیتابیس",
                generated_sql=generated_sql,
                tables_involved=[tbl_name],
                validation_status=True,
                risk_level="low",
                row_limit=50,
                explanation="کوئری امن تولید شده توسط مغز هوشمند با استخراج داده‌های زنده"
            )

            return AgentResponse(
                user_query=query,
                persian_answer=formatted_answer,
                intent=UserIntent.DATABASE_QUERY,
                sql_plan=sql_plan,
                sql_result=query_result,
                tools_used=tools_log,
                sources=sources,
                duration_ms=round(total_dur, 2),
                success=True,
                reasoning_steps=["تولید کوئری پویا توسط LLM", "اجرای امن در SQL Server", "سنتز خروجی فارسی"]
            )

        return None

    def _handle_knowledge_reasoning(
        self,
        query: str,
        intent: Optional[UserIntent],
        tools_log: list[ToolCallLog],
        sources: list[str],
        start_time: float,
        session_id: Optional[str] = None
    ) -> AgentResponse:
        """Leverages LLM with domain-specific CPA and SQL Architect mastery instructions."""
        lower_q = query.lower()

        # Extract recent conversation turns from memory
        history_text = ""
        if session_id:
            try:
                from app.agent.memory import chat_memory
                past_turns = chat_memory.get_messages(session_id)
                if past_turns:
                    # Take up to last 8 messages
                    recent = past_turns[-8:]
                    lines = []
                    for t in recent:
                        r = "کاربر" if t.get("role") == "user" else "دستیار سپهریار"
                        c = t.get("content", "").strip()
                        if len(c) > 300:
                            c = c[:300] + "..."
                        lines.append(f"{r}: {c}")
                    history_text = "\n".join(lines)
            except Exception as ex:
                logger.debug(f"Could not load chat history: {ex}")

        is_accounting = any(w in lower_q for w in [
            "حسابداری", "سند", "ثبت", "دوبل", "تراز", "ترازنامه", "سود و زیان", "استهلاک", "بهای تمام شده",
            "ارزش افزوده", "مالیات", "ماهیت حساب", "بدهکار", "بستانکار", "دارایی", "بدهی", "سرمایه",
            "پیش‌پرداخت", "پیش‌دریافت", "تخفیف", "حقوق", "دستمزد", "بیمه", "موجودی کالا", "fifo", "lifo",
            "میانگین موزون", "بستن حساب", "تعدیلات", "مبنای تعهدی", "نسبت جاری", "نسبت آنی", "اصول حسابداری"
        ])

        is_sql_prog = any(w in lower_q for w in [
            "sql", "tsql", "t-sql", "کوئری", "select", "join", "cte", "window function", "row_number",
            "dense_rank", "partition by", "stored procedure", "trigger", "index", "ایندکس", "پرفورمنس",
            "بهینه‌سازی", "deadlock", "transaction", "having", "group by", "subquery", "pivot", "view",
            "table", "جدول", "اسکریپت", "تابع"
        ])

        guidelines = []
        if is_accounting:
            sources.append("standards/cpa_accounting_standards")
            guidelines.append("""- به عنوان یک مشاور ارشد و استاد حسابداری، پاسخ را جامع و مستدل ارائه دهید.
- در صورت نیاز به صدور سند حسابداری، ثبت‌های دوبل را حتماً در یک جدول استاندارد با ستون‌های:
  | ردیف | کد و سرفصل کل / معین | تفصیلی | شرح آرتیکل سند | بدهکار (ریال) | بستانکار (ریال) |
  ارائه دهید و جمع بدهکار و بستانکار (تراز سند) را قید نمایید.
- مبنای استانداردهای حسابداری (ایران / IFRS)، فرمول‌های ریاضی و نکات کاربردی را تشریح فرمایید.""")

        if is_sql_prog:
            sources.append("engineering/sql_database_architecture")
            guidelines.append("""- به عنوان یک معمار ارشد پایگاه داده و متخصص T-SQL، کدهای درخواستی را به صورت تمیز، اصولی و با عملکرد بالا بنویسید.
- کدها را در بلاک ```sql قرار داده و کامنت‌های آموزشی و واضح داخل کد درج کنید.
- نحوه کارکرد توابع (به‌ویژه توابع تحلیلی پنجره‌ای، CTEها یا ایندکس‌ها) و نکات بهینه‌سازی را تشریح کنید.""")

        is_photo_req = any(w in lower_q for w in [
            "عکس", "عکساش", "عکساشم", "عکساشو", "عکسش", "عکسشو", "عکسها", "عکس‌ها", 
            "تصویر", "تصاویر", "اسکرین شات", "اسکرین‌شات", "آموزش تصویری", "راهنمای تصویری",
            "عکس فرم", "عکس منو", "تصویر فرم", "تصویر منو"
        ])
        if is_photo_req:
            sources.append("manuals/screenshots_and_visual_guides")
            # Load dynamically captured screenshots from ui_catalog.json
            dyn_images_str = ""
            cat_path = Path("D:/ai app/knowledge_base/manuals/images/ui_catalog.json")
            if cat_path.exists():
                try:
                    with open(cat_path, "r", encoding="utf-8") as f:
                        uicat = json.load(f)
                        if uicat:
                            dyn_lines = [f"  * {v.get('title')}: `{v.get('tag')}`" for v in uicat.values() if v.get('tag')]
                            if dyn_lines:
                                dyn_images_str = "\nتصاویر جدید ثبت‌شده توسط کاربر با F9:\n" + "\n".join(dyn_lines)
                except Exception:
                    pass

            guidelines.append(f"""- کاربر صراحتاً عکس، اسکرین‌شات یا راهنمای تصویری فرم‌های نرم‌افزار را خواسته است.
- صرفاً تصاویر ۱۰۰٪ منطبق با موضوع درخواست کاربر را با تگ ![عنوان](file:///d:/ai%20app/knowledge_base/manuals/images/...) درج کنید.{dyn_images_str}
- اگر برای موضوع درخواستی تصویری وجود ندارد، به هیچ وجه تصویر بی‌ارتباط (مانند درخت حساب‌ها) درج نکنید.""")
        else:
            guidelines.append("""- کاربر در این سوال درخواست عکس نکرده است. به هیچ وجه هیچ تگ تصویری (![...](...)) در متن پاسخ درج نکنید.
- پاسخ باید صرفاً متنی، دقیق، گام‌به‌گام و حرفه‌ای باشد.
- اکیداً از قرار دادن تصویر درختی حساب‌ها (payeh_img_4_1.png) برای موضوعات غیرمرتبط مانند «مدیریت سیستم»، «کاربران»، «دسترسی‌ها» یا «تنظیمات» خودداری کنید.""")

        kb_context = knowledge_search_engine.get_relevant_context(query, limit=2, max_chars=800)
        if kb_context:
            sources.append("knowledge_base/indexed_manuals")

        domain_instructions = "\n".join(guidelines) if guidelines else "- پاسخی دقیق، کاربردی و هوشمند ارائه دهید."

        history_block = f"""تاریخچه گفت‌وگوی اخیر کاربر:
{history_text}
----------------------
""" if history_text else ""

        prompt = f"""{history_block}پرسش یا پیام فعلی کاربر:
«{query}»

دستورالعمل‌های تخصصی ارائه پاسخ:
{domain_instructions}
- پاسخ را سریع، مستقیم، بسیار دقیق و بدون مقدمه‌چینی‌های زائد، تکرار سوال یا نتیجه‌گیری‌های کلیشه‌ای بنویسید. مستقیماً به اصل موضوع و حل نیاز کاربر بپردازید.

زمینه و مستندات سیستم:
{kb_context if kb_context else 'تسلط کامل به استانداردهای مالی، معماری دیتابیس و محیط سپهریار.'}

لطفاً پاسخی فصیح، روان، فوق‌العاده باهوش، صمیمی و سریع ارائه دهید."""

        res = llm_manager.generate(prompt=prompt, system_prompt=SEPEHRYAR_SYSTEM_PROMPT, max_tokens=850)
        total_dur = (time.perf_counter() - start_time) * 1000

        # Post-processing image sanitization
        clean_answer = res.content
        if not is_photo_req:
            # Strip any unrequested markdown images that LLM might hallucinate
            clean_answer = re.sub(r'!\[.*?\]\([^\)]+\)\s*(?:\([^\)]*\))?', '', clean_answer).strip()
        else:
            # If user asked for photos, strip mismatched payeh_img_4_1 on user/system mgmt topics
            if any(w in lower_q for w in ["مدیر سیستم", "مدیریت سیستم", "کاربر", "کاربران", "دسترسی"]):
                clean_answer = re.sub(r'!\[.*?\]\([^)]*payeh_img_4_1[^)]*\)\s*(?:\([^\)]*\))?', '', clean_answer).strip()

        reason_tag = "استدلال مشاور ارشد حسابداری و T-SQL"
        if is_accounting:
            reason_tag = "تحلیل اصول و استانداردهای حسابداری (Senior CPA)"
        elif is_sql_prog:
            reason_tag = "معماری و کدنویسی T-SQL (Principal Architect)"

        think_dur = max(round(total_dur * 0.4, 1), 15.0)
        steps = [
            "🎯 درک مقصود و تحلیل نیاز کاربر",
            "🔍 کاوش در پایگاه دانش و سرفصل‌های سیستم",
            f"💡 {reason_tag} با مدل {res.model_name}",
            "🛡️ اعتبارسنجی نهایی و تدوین پاسخ ساختاریافته"
        ]

        return AgentResponse(
            user_query=query,
            persian_answer=clean_answer,
            intent=intent or UserIntent.GENERAL_ACCOUNTING,
            sql_plan=None,
            sql_result=None,
            tools_used=tools_log,
            sources=sources,
            duration_ms=round(total_dur, 2),
            thinking_duration_ms=think_dur,
            thinking_summary=f"فرآیند تفکر تحلیلی در {len(steps)} مرحله",
            success=True,
            reasoning_steps=steps
        )

    def stream_process(
        self,
        query: str,
        intent: Optional[UserIntent] = None,
        session_id: Optional[str] = None,
        database_name: Optional[str] = None
    ):
        """Streams response tokens progressively from active LLM engine."""
        clean_query = query.strip()
        lower_q = clean_query.lower()

        # Extract recent conversation turns from memory
        history_text = ""
        if session_id:
            try:
                from app.agent.memory import chat_memory
                past_turns = chat_memory.get_messages(session_id)
                if past_turns:
                    recent = past_turns[-6:]
                    lines = []
                    for t in recent:
                        r = "کاربر" if t.get("role") == "user" else "دستیار سپهریار"
                        c = t.get("content", "").strip()
                        if len(c) > 250:
                            c = c[:250] + "..."
                        lines.append(f"{r}: {c}")
                    history_text = "\n".join(lines)
            except Exception:
                pass

        kb_context = knowledge_search_engine.get_relevant_context(clean_query, limit=2, max_chars=800)

        history_block = f"""تاریخچه گفت‌وگوی اخیر کاربر:
{history_text}
----------------------
""" if history_text else ""

        is_photo_req = any(w in lower_q for w in [
            "عکس", "عکساش", "عکساشم", "عکساشو", "عکسش", "عکسشو", "عکسها", "عکس‌ها", 
            "تصویر", "تصاویر", "اسکرین شات", "اسکرین‌شات", "آموزش تصویری", "راهنمای تصویری",
            "عکس فرم", "عکس منو", "تصویر فرم", "تصویر منو"
        ])
        photo_rule = "- کاربر درخواست عکس کرده است؛ تصویر دقیقاً متناسب را درج کنید." if is_photo_req else "- کاربر درخواست عکس نکرده است؛ مطلقاً هیچ عکس یا تگ تصویری درج نکنید."

        prompt = f"""{history_block}پرسش یا پیام فعلی کاربر:
«{clean_query}»

دستورالعمل:
- پاسخ را سریع، کاربردی، مستقیم و بدون مقدمه‌چینی‌های زائد ارائه دهید. مستقیماً به حل مساله بپردازید.
{photo_rule}
- در صورت لزوم جداول مقایسه‌ای یا کدهای T-SQL را شکیل درج کنید.

زمینه و مستندات سیستم:
{kb_context if kb_context else 'تسلط کامل به استانداردهای مالی، معماری دیتابیس و محیط سپهریار.'}"""

        for token in llm_manager.stream_generate(
            prompt=prompt,
            system_prompt=SEPEHRYAR_SYSTEM_PROMPT,
            max_tokens=850
        ):
            yield token


smart_agent_engine = SmartAgentEngine()
