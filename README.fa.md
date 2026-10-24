<div dir="rtl">

# persianprobe

**زبان برنامه‌نویسی‌ت متن فارسی رو همونطور که فکر می‌کنی پردازش می‌کنه؟** `persianprobe` یک مجموعه‌ی ۱۴ آزمایش یکسان (تبدیل `۱۲۳` به عدد، آیا `\d` با `۵` جور درمیاد، طول `نامه‌ها` چنده، آیا `علی` با `علي` برابره، `sort` حروف `ا ب پ ت` رو چطور مرتب می‌کنه، در JSON چطور نوشته می‌شه...) رو از همه‌ی runtimeهای نصب‌شده روی سیستمت (پایتون، Node، Bun، Perl، SQLite، jq، Go، awk) رد می‌کنه و یک جدول می‌ده: هرکدوم چی برمی‌گردونه، یک کاربر فارسی‌زبان چی انتظار داره، کجا runtimeها با هم فرق دارن و راه‌حل هرکدوم.

![python](https://img.shields.io/badge/python-3.9%2B-blue)
![deps](https://img.shields.io/badge/dependencies-none-brightgreen)
![license](https://img.shields.io/badge/license-MIT-lightgrey)

[English](README.md) | فارسی

</div>

```text
$ persianprobe --runtimes python,node,sqlite,go --probes parse-int,digit-regex,length,equal-ye,sort-default
persianprobe 0.1.0 · LC_ALL=C.UTF-8
  python  Python 3.13.5
  node    v20.19.2
  sqlite  SQLite 3.46.1
  go      go version go1.27.3 linux/amd64

probe         expected       python            node              sqlite            go
-----------------------------------------------------------------------------------------------------
parse-int     123            123 ✓             NaN ✗             0 ✗               error ✗
digit-regex   true           true ✓            false ✗           false ✗           false ✗
length        7              7 ✓               7 ✓               7 ✓               15 ✗
equal-ye      true           false ✗           false ✗           false ✗           false ✗
sort-default  alef be pe te  alef be te pe ✗   alef be te pe ✗   alef be te pe ✗   alef be te pe ✗
```


<div dir="rtl">

(مقدارهای فارسی در جدول به‌صورت لاتین نمایش داده می‌شن تا ستون‌ها در هر ترمینالی تراز بمونن؛ با `--raw` مقدار خام چاپ می‌شه. خروجی کامل و ویرایش‌نشده‌ی هر ۸ runtime در [docs/demo.txt](docs/demo.txt) هست.)

## چرا؟

متن فارسی نرم‌افزار رو بی‌صدا خراب می‌کنه. همون regex اعتبارسنجی در پایتون قبول می‌کنه و در جاوااسکریپت رد می‌کنه؛ `parseInt("۱۲۳")` می‌شه `NaN` ولی `int("۱۲۳")` می‌شه `123`، و `CAST` در SQLite بدون هیچ پیامی `0` برمی‌گردونه؛ `sort` پیش‌فرض «پ» رو بعد از «ت» می‌ذاره؛ `len` در Go بایت می‌شمره؛ کاربر «علي» (ی عربی) می‌نویسه و ایندکس یکتای تو الان دو تا «علی» داره. هر تیم اینا رو با یک گزارش باگ کشف می‌کنه و دستیارهای هوش مصنوعی هم نسخه‌ی انگلیسی‌شکلِ کد رو می‌نویسن. `persianprobe` واقعیتِ نسخه‌های نصب‌شده‌ی خودت رو یک‌جا می‌ذاره، با اجرای مفسرهای واقعی، نه نقل از یک پست وبلاگ.

## نصب

پایتون ۳٫۹ به بالا، بدون وابستگی. روی لینوکس تست شده؛ بقیه‌ی runtimeها اختیاری‌ان و اگه در `PATH` باشن استفاده می‌شن. ویندوز و macOS هنوز تست نشده.

</div>

```sh
pipx install git+https://github.com/mrzroot/persianprobe      # هنوز روی PyPI منتشر نشده
uvx --from git+https://github.com/mrzroot/persianprobe persianprobe
pip install -e .                                              # از یک کلون محلی
```

<div dir="rtl">

## استفاده

</div>

```sh
persianprobe                                  # همه‌ی آزمایش‌ها، همه‌ی runtimeهای پیداشده
persianprobe --runtimes python,node,sqlite    # فقط این‌ها
persianprobe --probes parse-int,sort-default  # فقط این آزمایش‌ها
persianprobe --list                           # آزمایش‌ها و دقیقاً کدی که برای هر runtime اجرا می‌شه
persianprobe --json                           # خروجی ماشینی
persianprobe --strict                         # اگه تله یا «هیچ‌کس درست نمی‌ده» باشه exit 1 (برای CI)
persianprobe --raw                            # مقدار خام
persianprobe --locale en_US.UTF-8             # LC_ALL برای پروسه‌های فرزند (پیش‌فرض C.UTF-8)

persianprobe xray "علي  كتاب‌ها ٤٥٦"           # کدوم کاراکترها شبیه‌ِ دیگری یا نامرئی‌ان
persianprobe xray -f pasted.txt --fix --digits en   # متن نرمال‌شده رو هم چاپ کن
```

<div dir="rtl">

## آزمایش‌ها

`parse-int`، `parse-int-sep`، `parse-float-dot`، `parse-float-fa-sep` (تبدیل `۱۲۳`، `۱٬۲۳۴`، `۱.۵`، `۱٫۵` با parser خودِ runtime)؛ `digit-regex` و `word-regex` (آیا `\d` با `۵` و `\w` با `ک` جور درمیاد)؛ `length` (طول `نامه‌ها`: ۷ نویسه، ۱۵ بایت)؛ `equal-ye` (آیا `علی` فارسی برابر `علي` عربیه)؛ `sort-default` و `sort-fa-locale` (مرتب‌سازی پیش‌فرض در برابر collation فارسی)؛ `json-encode`؛ `nfkc` (آیا `ﻻ` به `لا` تبدیل می‌شه)؛ `jalali-format` و `number-format-fa` (تاریخ جلالی و قالب اعداد `fa-IR`).

هر runtime همون کدی رو اجرا می‌کنه که یک برنامه‌نویس طبیعی می‌نویسه (`parseInt(s)`، `int(s)`، `/\d/`، `len(s)`) نه یک راه‌حل دورزننده؛ با `--list` می‌بینیش. آزمایشی که یک runtime اصلاً نمی‌تونه انجام بده `n/a` چاپ می‌کنه و **اختلاف** حساب نمی‌شه. حکم‌ها: **تله‌ی سازگاری** (بعضی درست، بعضی غلط)، **هیچ runtime درست نمی‌ده** و **شکاف قابلیت** (فقط بعضی اصلاً دارنش).

### xray

`persianprobe xray TEXT` نویسه‌های «درست‌نما ولی غلط» رو با جایگاه و کد یونیکد لیست می‌کنه: ي ى ك عربی، ارقام عربی-هندی (`٤٥٦` در برابر `۴۵۶`)، کشیده، فرم‌های نمایشی که از PDF/Word میان، علامت‌های نامرئیِ جهت، BOM، فاصله‌ی بدون شکست و ترکیب چند سیستم رقم. `--fix` متن نرمال‌شده رو چاپ می‌کنه (`--digits keep|fa|en`). همون تابع به‌صورت کتابخانه هم هست: `from persianprobe.xray import normalize`.

### به‌عنوان یک گام برای ایجنت‌ها

محتوای [docs/AGENTS.snippet.md](docs/AGENTS.snippet.md) رو در `AGENTS.md` / `CLAUDE.md` / قوانین Cursor بذار تا دستیار قبل از نوشتن نسخه‌ی انگلیسی‌شکلِ یک validator یا sort، رفتار فارسی رو بررسی کنه.

## محدودیت‌ها (لطفاً بخون)

- «انتظار» یعنی چیزی که یک کاربر فارسی‌زبان معمولاً انتظار داره و این یک *قضاوته*. مثلاً `equal-ye` که false می‌ده از نظر یونیکد درسته؛ چون کاربر رو غافلگیر می‌کنه و داده رو دو تکه می‌کنه فهرست شده. `json-encode` بیشتر سلیقه‌ست تا باگ. قبل از اقدام `why:` رو بخون.
- فقط می‌گه مفسرهای نصب‌شده **روی همین ماشین** چی می‌کنن، با `LC_ALL=C.UTF-8` به‌صورت پیش‌فرض (پایتون با `-X utf8`). نسخه، locale یا ICU دیگه ممکنه فرق کنه؛ `--locale` رو عوض کن و دوباره اجرا کن.
- adapter برای Ruby و PHP نیست (روی ماشین توسعه موجود نبودن و تست نشدن). adapter برای runtimeهای بیشتر قابل قبوله.
- `sort-fa-locale` برای پایتون به locale سیستم‌عاملِ `fa_IR.UTF-8` نیاز داره که اغلب سیستم‌ها ندارن: `-` نشون می‌ده.
- SQLite از طریق ماژول `sqlite3` پایتون اجرا می‌شه (همون موتور، بدون نیاز به CLI).
- فقط مفسرهای محلی رو اجرا می‌کنه، چیزی به شبکه نمی‌فرسته و فقط در یک پوشه‌ی موقت می‌نویسه.

## توسعه

</div>

```sh
pip install -e ".[test]" && pytest     # ۲۵ تست؛ تست runtimeهای غایب رد می‌شه
```

<div dir="rtl">

MIT · ساخته‌ی [Mohammadreza Zare (mrzroot)](https://github.com/mrzroot) · صفحه‌ی معرفی: https://mrzroot.github.io/persianprobe/

</div>
