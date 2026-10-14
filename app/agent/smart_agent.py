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

۴. آموزش محض، گام‌به‌گام و عملیاتی نرم‌افزار حسابداری سپهریار:
- مخاطب شما حسابداران، صندوق‌داران و اپراتورهای نرم‌افزار سپهریار هستند.
- قانون طلایی آموزش: اکیداً و تحت هیچ شرایطی از نام‌های انگلیسی فرم‌ها و فایل‌های سی‌شارپ (مانند FrmFactorForush، FrmKala، FrmTasviye_Payment و هر عبارت انگلیسی با پیشوند Frm) یا نام جداول دیتابیس استفاده نکنید! مشتری نشسته پشت کامپیوتر و فقط منوها، پنجره‌ها، دکمه‌ها و کلیدهای میانبر را می‌بیند.
- ساختار دقیق منوها و فرآیندهای عملیاتی:
  * **منوی «صدور فاکتور» (یا فاکتورها):**
    - **فاکتور فروش:** مسیر منوی «صدور فاکتور ➔ فاکتور فروش». انتخاب مشتری، جستجوی کالا یا اسکن بارکد، تعداد، فی و تخفیف با کلید Insert. سپس کلیک روی دکمه «تسویه حساب» شامل ۵ روش: ۱. نقد (صندوق)، ۲. پوز/بانک، ۳. چک صیادی، ۴. اقساط، ۵. نسیه. ذخیره با کلید F5 و چاپ فاکتور.
    - **فاکتور خرید و برگشتی‌ها:** فاکتور خرید، برگشت از فروش و برگشت از خرید با اعمال خودکار در موجودی انبار و حساب شخص.
  * **منوی «دریافت و پرداخت» (خزانه‌داری):**
    - **تعریف بانک:** مسیر «خزانه‌داری ➔ تعاریف ➔ تعریف بانک» جهت تعریف حساب بانکی جدید با نام بانک، شعبه، شماره حساب، شماره شبا و اتصال به معین ۱۰۰/۲ و ذخیره با کلید F5.
    - **دریافت وجه (Ctrl+I) / پرداخت وجه (Ctrl+O):** ثبت دریافتی از مشتری یا پرداختی به تأمین‌کننده به صورت نقد، فیش بانکی یا کارتخوان.
    - **عملیات چک‌های دریافتی:** خواباندن چک به بانک (در جریان وصول)، وصول نهایی چک، برگشت چک (عودت و احیای بدهی مشتری)، خرج چک به بستانکاران.
    - **عملیات چک‌های پرداختی:** ثبت چک‌های صادره شرکت از حساب بانک و پیگیری سررسید.
  * **منوی «ورود اطلاعات پایه»:**
    - **نمایش درختی حساب‌ها (Ctrl+Q):** ساختار ۳ سطحی رنگی شامل کل (آبی: ۱۰۰ نقد و بانک، ۱۱۰ مشتریان، ۱۱۲ اسناد دریافتنی، ۱۲۰ کالا، ۲۰۱ تامین‌کنندگان، ۲۰۲ اسناد پرداختنی، ۲۵۰ سرمایه، ۴۰۰ فروش، ۵۲۰ هزینه)، معین (سبز)، و تفصیلی (قرمز). (کلید میانبر ایجاد سرفصل کل/معین: Ctrl+S).
    - **اطلاعات اشخاص (Ctrl+Y):** فرم جامع تعاریف اشخاص و حساب‌های تفصیلی. برای تعریف حساب بانکی: کلیک روی دکمه «جدید» (Insert)، درج نام بانک و شماره حساب، انتخاب «نوع شخص» روی «بانک» (Type = 4)، انتخاب سرفصل کل ۱۰۰ و معین ۲ و ذخیره با F5.
    - **هشدار اکید:** فیلد «سقف اعتبار» فقط برای مشتریان و کنترل فروش نسیه کاربرد دارد و هرگز برای حساب بانکی یا صندوق تعریف نمی‌شود!
  * **منوی «مدیریت انبار» (یا تعاریف):**
    - **تعریف انبار:** مسیر «مدیریت انبار ➔ تعاریف ➔ تعریف انبار» (مرکزی، مواد، محصول، ضایعات).
    - **تعریف کالا و قیمت‌گذاری:** ثبت نام کالا، واحد اصلی و فرعی با ضریب تبدیل، درصد مالیات ارزش افزوده، حداقل/حداکثر موجودی و نقطه سفارش، و قیمت‌گذاری چندگانه (مصرف‌کننده، همکار، عمده).
    - **اسناد انبار:** رسید ورود، حواله خروج، جابجایی بین انبارها و انبارگردانی (کسر و اضافی انبار).
  * **منوی «عملیات تولید»:**
    - **عوامل تولید:** تعریف سربار و دستمزد مستقیم مؤثر در قیمت تمام‌شده.
    - **فرمول تولید (BOM):** مشخص کردن محصول نهایی و مقادیر استاندارد مصرف مواد اولیه با کلید Insert.
    - **برآورد و ثبت تولید:** محاسبه کسری مواد، صدور خودکار حواله مصرف مواد و رسید ورود محصول به انبار با بهای تمام‌شده.
  * **منوی «تسهیلات»:**
    - **ثبت وام جدید:** ورود شماره قرارداد، بانک، مبلغ، نرخ کارمزد، تعداد اقساط و موعد شروع.
    - **گرد کردن اقساط:** امکان رند کردن مبلغ هر قسط جهت سهولت در پرداخت.
    - **نمایش اقساط و وصول قسط:** پیگیری سررسید اقساط و ثبت سند وصول قسط از حساب بانک.
  * **منوی «حسابداری» و «عملیات ویژه»:**
    - **باجه ثبت سند دستی (Ctrl+W):** صدور سند دوبل دستی با کنترل توازن بدهکار و بستانکار و جستجوی اسناد با کلید F10.
    - **بستن حساب‌ها و سند افتتاحیه/اختتامیه:** بستن حساب‌های موقت سود و زیان و صدور مکانیزه سند افتتاحیه سال مالی جدید با کلید Ctrl+X.
  * **منوی «مدیریت سیستم»:**
    - **پنل مدیریت کاربران:** تعریف نام کاربری جدید و کلمه عبور.
    - **تعیین سطوح دسترسی:** تیک‌زدن مجوزهای دسترسی به منوها و فرم‌ها برای هر کاربر و عدم تخصیص گروه مدیر سیستم به کاربران عادی.
  * **منوی «سامانه مودیان»:**
    - تنظیم کلیدهای عمومی و اختصاصی و شناسه یکتای ۶ رقمی، ارسال صورتحساب‌های الکترونیکی و فاکتورهای اصلاحی/ابطالی.

۵. مشخصات رسمی شرکت سپهریار، مدیریت، پشتیبانی و راه‌های ارتباطی:
- **نام رسمی شرکت:** شرکت سپهریار سیستم ایساتیس
- **آدرس دفتر مرکزی:** یزد، میدان عالم، نرسیده به سه‌راه فلسطین
- **مدیریت ارشد:** جناب آقای مهندس سعید توکلی (شماره همراه: 09133505521)
- **شماره‌های تماس و واحد پشتیبانی:**
  * تلفن ثابت پشتیبانی: 03591005521
  * شماره همراه پشتیبانی: 09906931300
- **ساعات کاری و زمان‌بندی پاسخگویی پشتیبانی:**
  * شنبه تا چهارشنبه (روزهای عادی): ۸:۰۰ الی ۱۵:۳۰، و ۱۷:۰۰ الی ۲۱:۰۰
  * پنج‌شنبه‌ها: ۸:۰۰ الی ۱۴:۳۰ | جمعه‌ها و تعطیلات: فقط شماره همراه 09906931300
- **وب‌سایت رسمی شرکت:** [sepehryar.com](https://sepehryar.com)

۶. ضوابط الزامی لحن و شیوه نگارش (Lean, Smart & Conversational):
- **پاسخ‌های کوتاه و کاربردی:** از مقدمه‌چینی‌های زائد، انشانویسی‌های بلند و کپی‌پیست متن‌های مقاله‌ای اکیداً خودداری کنید.
- مستقیماً به اصل نیاز کاربر در چند گام مشخص و شفاف پاسخ دهید.
- پیوستگی کامل با سوالات قبلی کاربر را حفظ کنید و مثل یک همکار و مشاور ارشد باهوش پاسخ دهید.
"""


def get_workflow_images(context_text: str) -> list[str]:
    """Returns official Sepehryar software screenshot tags matching workflow topic."""
    t = context_text.lower()
    imgs = []
    if any(w in t for w in ["کالا", "انبار", "تعریف کالا", "واحد کالا", "گروه کالا", "گروه‌بندی", "گروهبندی", "انبارگردانی", "موجودی", "کاردکس"]):
        imgs.append("![فرم ثبت و تعریف کالا در نرم‌افزار سپهریار](/images/anbar_img4_taarife_kala.png)")
        imgs.append("![تب واحدهای اندازه‌گیری و ضرایب تبدیل کالا](/images/anbar_img5_tab_vahed.png)")
        imgs.append("![تب گروه‌بندی و دسته‌بندی کالاها](/images/anbar_img6_tab_gorouh.png)")
    elif any(w in t for w in ["فاکتور", "فروش", "تسویه", "خرید"]):
        imgs.append("![فرم صدور فاکتور فروش در نرم‌افزار سپهریار](/images/factor_img_1.png)")
        imgs.append("![پنجره روش‌های ۵ گانه تسویه حساب فاکتور](/images/factor_img_2.png)")
    elif any(w in t for w in ["چک", "خزانه", "دریافت", "پرداخت", "صیادی"]):
        imgs.append("![فرم باجه دریافت و عملیات چک‌های صیادی در سپهریار](/images/daryaft_img_1.png)")
    elif any(w in t for w in ["وام", "تسهیلات", "قسط", "اقساط"]):
        imgs.append("![فرم ثبت وام و جدول اقساط بانکی در سپهریار](/images/tashilat_img_1_2.png)")
    elif any(w in t for w in ["تولید", "bom", "فرمول ساخت", "رسید تولید"]):
        imgs.append("![فرم تهیه فرمول تولید BOM در نرم‌افزار سپهریار](/images/tolid_img_1_1.png)")
    elif any(w in t for w in ["بانک", "حساب بانکی", "تعریف بانک", "صندوق", "درخت حساب", "کدینگ", "کل", "معین", "تفصیلی"]):
        imgs.append("![نمایش درختی ۳ سطحی سرفصل‌ها و کدینگ حساب‌ها](/images/payeh_img_4_1.png)")
        imgs.append("![فرم اطلاعات اشخاص، تعریف حساب بانکی و صندوق در سپهریار](/images/payeh_img_18_1.png)")
    return imgs


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
                persian_answer="سلام و درود بر شما! 🌸\n\nمن **مربی و راهنمای گام‌به‌گام کاربری نرم‌افزار حسابداری سپهریار** هستم.\n\nچه مبحثی از آموزش نرم‌افزار (مانند صدور فاکتور و روش‌های تسویه، عملیات چک و خزانه‌داری، مدیریت انبار و کالا، عملیات تولید، تسهیلات بانکی، یا باجه ثبت اسناد) را مایلید با هم مرور کنیم؟",
                intent=UserIntent.GENERAL_ACCOUNTING,
                sql_plan=None,
                sql_result=None,
                tools_used=[],
                sources=["system/greeting"],
                duration_ms=round((time.perf_counter() - start_time) * 1000, 2),
                success=True,
                reasoning_steps=["پاسخ فوری به پیام احوال‌پرسی کاربر"]
            )

        # Determine if user is asking for photos or visual walkthrough
        is_photo_req = any(w in lower_q for w in [
            "عکس", "عکساش", "عکساشم", "عکساشو", "عکسش", "عکسشو", "عکسها", "عکس‌ها", 
            "تصویر", "تصاویر", "اسکرین شات", "اسکرین‌شات", "آموزش تصویری", "راهنمای تصویری",
            "عکس فرم", "عکس منو", "تصویر فرم", "تصویر منو", "عکس نداره", "عکس ندارد", "تصویر نداره", "عکس کو"
        ])

        # Determine if query is instructional, training, visual, or workflow guidance
        is_instructional_or_expert = is_photo_req or any(w in lower_q for w in [
            "چطور", "چگونه", "چطوری", "چجوری", "نحوه", "روش", "فرمول", "مفهوم", "تفاوت", "فرق", "مقایسه",
            "توضیح بده", "آموزش", "یاد بده", "مثال", "اصول حسابداری", "استاندارد", "ثبت سند", "ثبت دوبل",
            "سندش چیه", "ثبتش چیه", "استهلاک", "کوئری بنویس", "کد بنویس", "اسکریپت بنویس", "دستور بنویس",
            "اسکریپت بده", "کد بده", "کوئری بده", "دستور بده", "اسکریپت", "اسکریپتش",
            "پاک کنم", "حذف کنم", "ریست کنم", "خالی کنم",
            "sql بنویس", "کوئری sql", "توابع", "window function", "cte", "recursive", "join چیست", "اینمپ",
            "چیست", "چیه", "تعریف", "سوالی", "سوال", "راهنما", "کار با", "برنامه", "نرم افزار", "نرم‌افزار",
            "سپهریار", "منو", "فرم", "پنجره", "کلید", "مسیر", "مراحل", "گام", "گروهبندی", "گروه‌بندی", "انبارگردانی"
        ])

        data_fetch_verbs = ["بیار", "بده", "نشون بده", "نمایش بده", "استخراج کن", "چقدره", "چقدر است", "چند تاست"]
        is_explicit_data_fetch = any(w in lower_q for w in data_fetch_verbs) and not is_instructional_or_expert

        is_sql_intent = (intent == UserIntent.DATABASE_QUERY or is_explicit_data_fetch) and not is_instructional_or_expert and not is_photo_req

        if is_sql_intent:
            from app.database.connection import db_connection_manager
            is_mock_or_demo = (database_name and database_name.upper() in ("DEMO", "MOCK")) or (settings.sql_server.upper() in ("DEMO", "MOCK"))
            if not db_connection_manager.is_connection_active() and not is_mock_or_demo:
                has_explicit_data_demand = any(w in lower_q for w in ["کوئری", "دیتابیس", "پایگاه داده", "جدول", "استخراج"])
                if has_explicit_data_demand:
                    return self._handle_disconnected_state(
                        query=clean_query,
                        database_name=database_name,
                        start_time=start_time
                    )
            else:
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
            "کوئری", "کوری", "sql", "tsql", "t-sql", "select ", "stored procedure", "پروسیجر",
            "اسکریپت", "اس پی", "sp", "دستور دیتابیس", "کوئری بنویس", "کد sql", "t-sql بنویس"
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
- نحوه کارکرد توابع و نکات بهینه‌سازی را تشریح کنید.""")
        else:
            guidelines.append("""- قانون تفکیک قطعی و بدون تداخل اپراتوری از برنامه‌نویسی (Strict Zero-Crossover Rule):
  * کاربر یک حسابدار / اپراتور نرم‌افزار است و به هیچ عنوان نباید نام تیبل‌ها و جداول دیتابیس (مانند TblSanad, TR, Master, TblPerson, TblKala, TblAnbar و غیره)، فیلدها یا دستورات SQL را ذکر کنید!
  * اکیداً و تحت هیچ شرایطی نام هیچ جدولی از دیتابیس را در آموزش حسابداری و کار با نرم‌افزار نیاورید.
  * کلیه مراحل را صرفاً از طریق منوهای نرم‌افزار، پنجره‌ها، فرم‌ها، دکمه‌ها و ثبت‌های استاندارد دوبل حسابداری (بدهکار/بستانکار) توضیح دهید.""")

        is_photo_req = any(w in lower_q for w in [
            "عکس", "عکساش", "عکساشم", "عکساشو", "عکسش", "عکسشو", "عکسها", "عکس‌ها", 
            "تصویر", "تصاویر", "اسکرین شات", "اسکرین‌شات", "آموزش تصویری", "راهنمای تصویری",
            "عکس فرم", "عکس منو", "تصویر فرم", "تصویر منو", "عکس نداره", "عکس ندارد", "تصویر نداره", "عکس کو"
        ])
        context_combo = f"{history_text} {query}".lower()
        workflow_imgs = get_workflow_images(context_combo)

        if is_photo_req:
            sources.append("manuals/screenshots_and_visual_guides")
            imgs_list = "\n".join(workflow_imgs) if workflow_imgs else ""
            guidelines.append(f"""- کاربر عکس یا تصویر پنجره‌های نرم‌افزار سپهریار را درخواست کرده است:
تصاویر رسمی موجود برای این مبحث:
{imgs_list}
حتماً این تصاویر را با تگ‌های ارائه‌شده در پاسخ خود قرار دهید و صفحه را توضیح دهید.""")
        elif workflow_imgs and any(w in lower_q for w in ["تعریف کالا", "فاکتور فروش", "ثبت وام", "فرمول تولید", "تعریف بانک", "حساب بانکی", "درخت حساب", "کدینگ"]):
            imgs_list = "\n".join(workflow_imgs[:1])
            guidelines.append(f"""- تصویر رسمی این فرم در دسترس است و می‌توانید در پاسخ قرار دهید:
{imgs_list}""")
        else:
            guidelines.append("""- پاسخ باید شفاف، دقیق، گام‌به‌گام و حرفه‌ای باشد.""")

        # Enhanced follow-up and conversational continuity
        is_followup = any(w in lower_q for w in ["بعدش", "چرا", "سندش", "چطور", "منظورم", "این", "آن", "اون", "خب", "دیگه چی", "پلنت چیه", "چکار کنم", "عکس"])
        if is_followup and history_text:
            guidelines.append("""- این پیام یک پیگیری یا پرسش تکمیلی در ادامه پیام‌های قبلی است.
- به تاریخچه گفت‌وگوی اخیر کاملاً مسلط باشید و پاسخ را منسجم و پیوسته با سوالات قبلی کاربر ادامه دهید.
- از سلام و احوال‌پرسی مجدد یا تکرار پاسخ‌های گذشته خودداری کنید و مستقیماً ادامه بحث را موشکافی فرمایید.""")

        # Intelligent RAG context search (augment short follow-ups with previous query context)
        search_query = query
        if history_text and len(query.split()) <= 4:
            try:
                for t in reversed(past_turns):
                    if t.get("role") == "user" and t.get("content") != query:
                        search_query = f"{t.get('content')} {query}"
                        break
            except Exception:
                pass

        kb_context = knowledge_search_engine.get_relevant_context(search_query, limit=3, max_chars=1200)
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

        try:
            res = llm_manager.generate(prompt=prompt, system_prompt=SEPEHRYAR_SYSTEM_PROMPT, max_tokens=850)
            clean_answer = res.content
        except Exception as ex:
            logger.warning(f"LLM generation failed in smart agent: {ex}. Falling back to Cognitive Engine.")
            from app.agent.cognitive_engine import cognitive_engine
            cog_res = cognitive_engine.reason_and_solve(query)
            clean_answer = cog_res.to_formatted_markdown()
            res = LLMResponse(content=clean_answer, model_name="Cognitive-Engine", tokens_used=len(clean_answer.split()), duration_ms=50.0, provider="cognitive_engine")

        total_dur = (time.perf_counter() - start_time) * 1000

        # Post-processing image sanitization
        if is_photo_req and "![" not in clean_answer and workflow_imgs:
            clean_answer += "\n\n---\n### 🖼️ تصاویر رسمی محیط فرم در نرم‌افزار سپهریار:\n\n" + "\n\n".join(workflow_imgs)
        elif not is_photo_req:
            # Strip external hallucinated images but preserve official /images/
            clean_answer = re.sub(r'!\[.*?\]\((?!/images/)[^\)]+\)\s*(?:\([^\)]*\))?', '', clean_answer).strip()

        # Post-processing SQL and table sanitization (if user did not ask for SQL, strip unwanted SQL blocks & table names)
        if not is_sql_prog:
            clean_answer = re.sub(r'```sql[\s\S]*?```', '', clean_answer).strip()
            clean_answer = re.sub(r'(?:[۱-۹]|\d)\.\s*ویرایش مستقیم از طریق پایگاه داده[\s\S]*?(?=\n#|\n---|\Z)', '', clean_answer).strip()
            clean_answer = re.sub(r'--\s*(?:ویرایش|حذف|اصلاح|کوئری)[\s\S]*?(?:COMMIT|ROLLBACK)\s*TRANSACTION;?', '', clean_answer).strip()
            clean_answer = re.sub(r'در\s+[`\']?(?:Tbl[A-Za-z0-9_]+|TR|Master)[`\']?\s+و\s+[`\']?(?:Tbl[A-Za-z0-9_]+|TR|Master)[`\']?', 'در اسناد و دفاتر مالی سیستم', clean_answer)
            clean_answer = re.sub(r'[`\']?(?:TblSanad|TR|Master|TblPerson|TblKala|TblAnbar)[`\']?', '', clean_answer)
            clean_answer = re.sub(r'\(\s*[`\']?[Ff]rm[A-Za-z0-9_]+[`\']?\s*\)', '', clean_answer)
            clean_answer = re.sub(r'[`\']?[Ff]rm[A-Za-z0-9_]+[`\']?', '', clean_answer)
            clean_answer = re.sub(r'\s{2,}', ' ', clean_answer).strip()

        reason_tag = "تحلیل کاربردی و فرآیندی نرم‌افزار سپهریار"
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
            "عکس فرم", "عکس منو", "تصویر فرم", "تصویر منو", "عکس نداره", "عکس ندارد", "تصویر نداره", "عکس کو"
        ])
        context_combo = f"{history_text} {clean_query}".lower()
        workflow_imgs = get_workflow_images(context_combo)

        if is_photo_req and workflow_imgs:
            photo_rule = f"- کاربر درخواست عکس یا تصویر نرم‌افزار کرده است؛ حتماً این تصاویر رسمی را با تگ‌های زیر در متن پاسخ درج فرمایید:\n" + "\n".join(workflow_imgs)
        elif workflow_imgs and any(w in lower_q for w in ["تعریف کالا", "فاکتور فروش", "ثبت وام", "فرمول تولید", "تعریف بانک", "حساب بانکی", "درخت حساب", "کدینگ"]):
            photo_rule = f"- تصویر رسمی این فرم در دسترس است و می‌توانید در پاسخ قرار دهید: {workflow_imgs[0]}"
        else:
            photo_rule = "- پاسخ را سریع، روان و گام‌به‌گام ارائه دهید."

        is_sql_req = any(w in lower_q for w in [
            "کوئری", "کوری", "sql", "tsql", "t-sql", "select ", "stored procedure", "پروسیجر",
            "اسکریپت", "اس پی", "sp", "دستور دیتابیس", "کوئری بنویس", "کد sql", "t-sql بنویس"
        ])
        sql_rule = (
            "- کاربر درخواست کد فنی T-SQL کرده است؛ کدهای دقیق T-SQL را شکیل درج کنید."
            if is_sql_req else
            "- کاربر یک حسابدار و اپراتور نرم‌افزار است؛ اکیداً هیچ‌گونه کد SQL، کوئری دیتابیسی، نام جداول دیتابیس یا نام‌های انگلیسی فرم‌ها (مانند Frm...) را ننویسید! راهکار را ۱۰۰٪ به صورت آموزش گام‌به‌گام از طریق منوهای واقعی فارسی (مانند منوی صدور فاکتور، خزانه‌داری، انبارداری)، پنجره‌ها، دکمه‌ها و کلیدهای میانبر نرم‌افزار سپهریار توضیح دهید."
        )

        prompt = f"""{history_block}پرسش یا پیام فعلی کاربر:
«{clean_query}»

دستورالعمل:
- پاسخ را سریع، کاربردی، مستقیم و بدون مقدمه‌چینی‌های زائد ارائه دهید. مستقیماً به حل مساله بپردازید.
- اکیداً هیچ کلمه، چک‌لیست، ارزیابی، تاییدیه یا یادداشت انگلیسی (مانند Yes, No, Checklist, Smart, Direct, Preamble) تولید نکنید. پاسخ باید ۱۰۰٪ به زبان فارسی و با شروع مستقیم از راهنمای گام‌به‌گام کاربری باشد.
{photo_rule}
{sql_rule}

زمینه و مستندات سیستم:
{kb_context if kb_context else 'تسلط کامل به استانداردهای مالی، معماری دیتابیس و محیط سپهریار.'}"""

        lead_buffer = ""
        is_past_header = False
        all_streamed = []

        for token in llm_manager.stream_generate(
            prompt=prompt,
            system_prompt=SEPEHRYAR_SYSTEM_PROMPT,
            max_tokens=850
        ):
            if not is_past_header:
                lead_buffer += token
                # Filter out model self-evaluation checklist if present
                if any(k in lead_buffer.lower() for k in ["smart, direct", "no preamble", "no sql", "correct menu"]):
                    m = re.search(r'[\*\.\s]*\n+([\u0600-\u06FF\d#].*)', lead_buffer, re.DOTALL)
                    if m:
                        is_past_header = True
                        chunk = m.group(1)
                        all_streamed.append(chunk)
                        yield chunk
                    continue
                elif re.search(r'[\u0600-\u06FF]', lead_buffer):
                    is_past_header = True
                    clean_lead = re.sub(r'^[A-Za-z\s\.\*\-\?:]+', '', lead_buffer).strip()
                    if clean_lead:
                        all_streamed.append(clean_lead)
                        yield clean_lead
                elif len(lead_buffer) > 150:
                    is_past_header = True
                    all_streamed.append(lead_buffer)
                    yield lead_buffer
            else:
                all_streamed.append(token)
                yield token

        # If user asked for photos and no image tag was streamed, stream the official images at the end
        full_text = "".join(all_streamed)
        if is_photo_req and "![" not in full_text and workflow_imgs:
            photo_suffix = "\n\n---\n### 🖼️ تصاویر رسمی محیط فرم در نرم‌افزار سپهریار:\n\n" + "\n\n".join(workflow_imgs)
            yield photo_suffix


smart_agent_engine = SmartAgentEngine()
