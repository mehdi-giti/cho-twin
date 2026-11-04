// English -> Persian (fa) for the CHO twin page. Exact phrases + pattern rules for text that carries numbers.
// The page is written in English; when Persian is chosen every text node and label is translated in place,
// and re-translated whenever the page redraws. Digits stay Latin (scientific values, units, version numbers).
(function (root) {
  "use strict";
  const EX = {
    // header + navigation
    "Bioprocess digital twin · MVP": "دوقلوی دیجیتال فرایند زیستی · نسخهٔ اولیه",
    "CHO Fed-Batch Twin": "دوقلوی دیجیتال کشت خوراک‌دهی‌شدهٔ CHO",
    "mAb (IgG1κ) · 20 mL fed-batch, 37 °C · hybrid model": "آنتی‌بادی تک‌دودمانی (IgG1κ) · کشت خوراک‌دهی‌شدهٔ ۲۰ میلی‌لیتری، 37 °C · مدل ترکیبی",
    "Plan a run": "طراحی کشت", "Batches": "بچ‌ها", "Model": "مدل",
    // run plan
    "Combined": "ترکیبی", "Separate": "جداگانه", "All series on one chart": "همهٔ سری‌ها در یک نمودار", "One chart per output, with 80% bands": "یک نمودار برای هر خروجی، با بازه‌های ۸۰٪", "Chart view": "نمای نمودار", "+ Add series…": "+ افزودن سری…", "Add series": "افزودن سری",
    "Inputs: step lines": "ورودی‌ها: خطوط پله‌ای", "Feed": "خوراک", "Fill with a real run…": "پر کردن با یک کشت واقعی…",
    "Every series has its own scale (axis limits above). Hover to read all values for one day. Prediction bands are shown in the separate view.": "هر سری مقیاس خود را دارد (حدود محورها در بالا). برای دیدن همهٔ مقادیر یک روز، نشانگر را روی نمودار ببرید. بازه‌های پیش‌بینی در نمای جداگانه نمایش داده می‌شوند.",
    // running batch
    "New plan": "برنامهٔ جدید", "Running batch": "بچ در حال اجرا", "Mode": "حالت",
    "Measured up to day (today)": "اندازه‌گیری‌شده تا روز (امروز)", "Viab.": "زنده‌مانی", "Lac": "لاکتات",
    "Morning samples, before that day's feed; leave blank what was not measured. The inputs already applied on days before today go in the day table below.": "نمونه‌های صبح، پیش از خوراک همان روز؛ آنچه اندازه‌گیری نشده را خالی بگذارید. ورودی‌های اعمال‌شده در روزهای پیش از امروز در جدول روزانهٔ پایین وارد می‌شوند.",
    "Fill with a real run…": "پر کردن با یک کشت واقعی…", "Paste CSV": "چسباندن CSV", "Clear": "پاک‌کردن", "Use pasted data": "استفاده از دادهٔ چسبانده‌شده",
    "Measured values per day": "مقادیر اندازه‌گیری‌شدهٔ روزانه", "Running batch CSV": "CSV بچ در حال اجرا", "Fill with a real run": "پر کردن با یک کشت واقعی",
    "Self-adjusted to this run:": "تنظیم خودکار با این کشت:", "Enter at least the day-0 VCD to use the measured data.": "برای استفاده از داده‌ها دست‌کم VCD روز ۰ را وارد کنید.",
    "Suggest inputs from today": "پیشنهاد ورودی‌ها از امروز", "Keep final viability ≥": "زنده‌مانی نهایی ≥", "Allow a temperature shift (literature prior)": "اجازهٔ تغییر دما (بر پایهٔ منابع علمی)",
    "Find best inputs": "یافتن بهترین ورودی‌ها", "Searching…": "در حال جست‌وجو…", "Suggested inputs": "ورودی‌های پیشنهادی",
    "The search tries every combination of feeding every 24 h (2.5%) or 48 h (5%), glucose top-up 2–8 g/L, Gal+ on or off and, if allowed, a shift to 33–35 °C, and ranks them by predicted day-11 titer. Each setting was tested in real runs, but most combinations were not: treat a suggestion as the next experiment to run, not a guaranteed result.": "جست‌وجو همهٔ ترکیب‌های خوراک‌دهی هر ۲۴ ساعت (۲٫۵٪) یا هر ۴۸ ساعت (۵٪)، تکمیل گلوکز 2 تا 8 g/L، Gal+ روشن یا خاموش و در صورت اجازه، کاهش دما به 33 تا 35 °C را می‌آزماید و آن‌ها را بر اساس تیتر پیش‌بینی‌شدهٔ روز ۱۱ رتبه‌بندی می‌کند. هر تنظیم در کشت‌های واقعی آزموده شده، اما بیشتر ترکیب‌ها نه: پیشنهاد را آزمایش بعدی بدانید، نه نتیجهٔ تضمینی.",
    "g/L predicted titer, day 11": "g/L تیتر پیش‌بینی‌شده، روز ۱۱", "Apply to plan": "اعمال بر برنامه", "Applied": "اعمال شد", "Applied ✓": "اعمال شد ✓",
    "settings within real data": "تنظیمات در محدودهٔ داده‌های واقعی", "uses a literature prior": "بر پایهٔ منابع علمی", "Feed 2.5% every day": "خوراک ۲٫۵٪ هر روز", "Feed 5% every 48 h": "خوراک ۵٪ هر ۴۸ ساعت",
    "no glucose top-up": "بدون تکمیل گلوکز", "with Gal+": "با Gal+", "no Gal+": "بدون Gal+", "37 °C": "37 °C",
    "Measured · this run": "اندازه‌گیری‌شده · این کشت", "Measured, this run:": "اندازه‌گیری‌شده، این کشت:", "today": "امروز",
    "Already done: measured data used": "انجام‌شده: دادهٔ اندازه‌گیری‌شده استفاده شد",
    "Could not read the pasted data: a time_h column is needed.": "دادهٔ چسبانده‌شده خوانده نشد: ستون time_h لازم است.",
    "Run plan": "برنامهٔ کشت", "11-day culture": "کشت ۱۱ روزه",
    "Start from a real feeding strategy": "شروع از یک راهبرد تغذیهٔ واقعی",
    "Feed 5% every 48 h from day 3, glucose topped up to 8 g/L. Highest real titers.": "خوراک ۵٪ هر ۴۸ ساعت از روز ۳، گلوکز تا 8 g/L تکمیل می‌شود. بالاترین تیتر واقعی.",
    "As STD, plus galactose and Mn²⁺ with every other feed.": "مانند STD، به‌علاوهٔ گالاکتوز و Mn²⁺ در یک‌درمیان خوراک‌ها.",
    "Feed 5% every 48 h, glucose only to 4 g/L. Real cultures collapsed after glucose ran out.": "خوراک ۵٪ هر ۴۸ ساعت، گلوکز فقط تا 4 g/L. کشت‌های واقعی پس از تمام‌شدن گلوکز فروپاشیدند.",
    "As LoG, plus galactose. Galactose bridges part of the glucose gap.": "مانند LoG، به‌علاوهٔ گالاکتوز. گالاکتوز بخشی از کمبود گلوکز را جبران می‌کند.",
    "Feed 2.5% every day from day 3, glucose to 4 g/L.": "خوراک ۲٫۵٪ هر روز از روز ۳، گلوکز تا 4 g/L.",
    "Feed 2.5% every day, glucose to 2 g/L only when depleted (HIPDOG-like).": "خوراک ۲٫۵٪ هر روز، گلوکز فقط هنگام اتمام تا 2 g/L (شبیه HIPDOG).",
    "As HIP, plus galactose. Never used for training: the model's unseen test recipe.": "مانند HIP، به‌علاوهٔ گالاکتوز. هرگز در آموزش استفاده نشده: دستورالعمل آزمون نادیدهٔ مدل.",
    "Feed volume": "حجم خوراک", "0 = no feed · real runs used 2.5–5% v/v": "0 = بدون خوراک · کشت‌های واقعی 2.5 تا 5% v/v",
    "no feed": "بدون خوراک", "Glucose top-up to": "تکمیل گلوکز تا", "no top-up": "بدون تکمیل",
    "0 = no top-up · real runs used 2–8 g/L": "0 = بدون تکمیل · کشت‌های واقعی 2 تا 8 g/L",
    "Temperature": "دما", "real runs: 37 °C only · other values use literature": "کشت‌های واقعی: فقط 37 °C · مقادیر دیگر از منابع علمی",
    "Galactose + Mn²⁺ (Gal+) with this feed": "گالاکتوز + Mn²⁺ (Gal+) همراه این خوراک",
    "pH control": "کنترل pH", "Dissolved oxygen control": "کنترل اکسیژن محلول", "off": "خاموش",
    "off = as in the reference runs (not controlled) · effect is a literature prior": "خاموش = مانند کشت‌های مرجع (بدون کنترل) · اثر بر پایهٔ منابع علمی است",
    "% air saturation · literature prior + one real low-DO run": "% اشباع هوا · بر پایهٔ منابع علمی + یک کشت واقعی با DO پایین",
    "recipe: not controlled": "دستورالعمل: بدون کنترل",
    "Agitation is not an input yet: no runs separate its effect from DO. Batch files can record it (": "هم‌زدن هنوز ورودی مدل نیست: هیچ کشتی اثر آن را از DO جدا نمی‌کند. فایل‌های بچ می‌توانند آن را ثبت کنند (ستون ",
    "column) so a later model can learn it.": ") تا مدل‌های بعدی آن را یاد بگیرند.",
    "Click a day to edit it. Inputs act at the start of each day, after the morning sample. Edited values are shown in colour.": "برای ویرایش، روی یک روز کلیک کنید. ورودی‌ها در آغاز هر روز، پس از نمونه‌برداری صبح، اعمال می‌شوند. مقادیر ویرایش‌شده رنگی نمایش داده می‌شوند.",
    "Day": "روز", "Feed": "خوراک", "Glc": "گلوکز", "Temp": "دما", "pH": "pH", "DO": "DO", "Gal+": "Gal+",
    "Within real data": "در محدودهٔ داده‌های واقعی", "Literature prior (temperature, pH, DO)": "بر پایهٔ منابع علمی (دما، pH، DO)",
    "Outside tested range": "خارج از محدودهٔ آزموده‌شده",
    "Seed VCD": "VCD تلقیح", "Seed viability": "زنده‌مانی تلقیح",
    "Reset to recipe": "بازگشت به دستورالعمل", "Keep as comparison": "نگه‌داشتن برای مقایسه", "Clear comparison": "پاک‌کردن مقایسه",
    // readout
    "Predicted titer · day 11": "تیتر پیش‌بینی‌شده · روز ۱۱", "Predicted peak VCD": "بیشینهٔ VCD پیش‌بینی‌شده",
    "Predicted viability · day 11": "زنده‌مانی پیش‌بینی‌شده · روز ۱۱", "Basis of this prediction": "پشتوانهٔ این پیش‌بینی",
    "Measured:": "اندازه‌گیری‌شده:", "Predicted · this plan": "پیش‌بینی‌شده · این برنامه", "80% range of the prediction": "بازهٔ ۸۰٪ پیش‌بینی",
    "Measured real runs": "کشت‌های واقعی اندازه‌گیری‌شده", "80% range": "بازهٔ ۸۰٪", "Predicted:": "پیش‌بینی‌شده:", "Predicted": "پیش‌بینی‌شده",
    "Axis limits (fixed, so the scale stays put while you change inputs)": "حدود محورها (ثابت، تا با تغییر ورودی‌ها مقیاس جابه‌جا نشود)",
    "Output": "خروجی", "Min": "کمینه", "Max": "بیشینه", "Reset to defaults": "بازگشت به پیش‌فرض",
    "Values above a limit show as ▲ off scale.": "مقادیر بالاتر از حد با ▲ خارج از مقیاس نشان داده می‌شوند.",
    "Titer": "تیتر", "Viable cell density": "چگالی سلول‌های زنده", "Viability": "زنده‌مانی", "Glucose": "گلوکز", "Lactate": "لاکتات",
    "Bands show the 80% range, calibrated on real runs the model never trained on; they widen the further ahead the twin predicts. Glucose is shown as sampled, before that day's feed.": "نوارها بازهٔ ۸۰٪ را نشان می‌دهند که روی کشت‌های واقعیِ استفاده‌نشده در آموزش کالیبره شده است؛ هرچه پیش‌بینی دورتر باشد، پهن‌تر می‌شوند. گلوکز همان مقدار نمونه‌برداری‌شده پیش از خوراک آن روز است.",
    "Daily values as a table": "مقادیر روزانه به‌صورت جدول",
    "Predicted titer (g/L)": "تیتر پیش‌بینی‌شده (g/L)", "Predicted viable cell density (10⁶ cells/mL)": "چگالی سلول زندهٔ پیش‌بینی‌شده (10⁶ cells/mL)",
    "Predicted viability (%)": "زنده‌مانی پیش‌بینی‌شده (%)", "Predicted glucose (g/L)": "گلوکز پیش‌بینی‌شده (g/L)", "Predicted lactate (g/L)": "لاکتات پیش‌بینی‌شده (g/L)",
    // batches
    "Import a batch": "ورود یک بچ",
    "One CSV per culture. The twin checks it and predicts it from day 0 before anything is saved, so you see how well the current model would have done. Nothing leaves your browser while you check.": "برای هر کشت یک فایل CSV. دوقلو پیش از ذخیره آن را بررسی و از روز ۰ پیش‌بینی می‌کند تا ببینید مدل فعلی چقدر دقیق بوده است. هنگام بررسی هیچ داده‌ای از مرورگر شما خارج نمی‌شود.",
    "Drop a CSV file here": "فایل CSV را اینجا رها کنید", "or": "یا", "choose a file": "یک فایل انتخاب کنید",
    "Load a real example run…": "بارگذاری یک کشت واقعی نمونه…", "Paste text": "چسباندن متن", "Check pasted data": "بررسی دادهٔ چسبانده‌شده",
    "File format": "قالب فایل", "hours since inoculation, first row 0": "ساعت از تلقیح، ردیف اول 0",
    "viable cells, 10⁶ cells/mL (row 0 required)": "سلول‌های زنده، 10⁶ cells/mL (ردیف 0 الزامی)",
    "glucose, lactate": "glucose، lactate", "g/L, measured before that day's feed": "g/L، اندازه‌گیری پیش از خوراک آن روز",
    "feed added right after this sample, % v/v (0 = none)": "خوراک افزوده‌شده درست پس از این نمونه، % v/v (0 = هیچ)",
    "glucose topped up to, g/L (blank = none)": "گلوکز تکمیل‌شده تا، g/L (خالی = هیچ)",
    "1 if galactose + Mn²⁺ added with this feed": "1 اگر گالاکتوز + Mn²⁺ با این خوراک افزوده شد",
    "°C from this sample to the next": "°C از این نمونه تا نمونهٔ بعد",
    "pH, DO, agitation": "pH، DO، هم‌زدن",
    "optional set-points from this sample to the next (pH units, % air saturation, rpm); blank = not controlled or not recorded": "نقطه‌تنظیم‌های اختیاری از این نمونه تا نمونهٔ بعد (واحد pH، % اشباع هوا، rpm)؛ خالی = بدون کنترل یا ثبت‌نشده",
    "Blank cells mean not measured. Optional first lines:": "خانهٔ خالی یعنی اندازه‌گیری نشده. خطوط اختیاری ابتدای فایل:",
    "Copy template": "کپی الگو", "Copied": "کپی شد",
    "Choose a file or load an example run to check it.": "یک فایل انتخاب کنید یا یک کشت نمونه بارگذاری کنید.",
    "Nothing is saved until you press Save.": "تا دکمهٔ ذخیره را نزنید چیزی ذخیره نمی‌شود.",
    "Predicted first, with model": "پیش‌بینی پیشاپیش، با مدل", "Titer error": "خطای تیتر", "VCD error": "خطای VCD",
    "Viability error": "خطای زنده‌مانی", "points": "امتیاز", "Inside 80% band": "درون بازهٔ ۸۰٪",
    "Line and band: the twin's forecast from day 0 using only this batch's inputs. Points: what was measured.": "خط و نوار: پیش‌بینی دوقلو از روز ۰ فقط با ورودی‌های همین بچ. نقطه‌ها: مقادیر اندازه‌گیری‌شده.",
    "Save batch for retraining": "ذخیرهٔ بچ برای آموزش مجدد", "Download for upload": "دانلود برای بارگذاری",
    "Already stored, so there is nothing to save.": "قبلاً ذخیره شده است؛ چیزی برای ذخیره نیست.",
    "Fix the errors above, then check the file again.": "خطاهای بالا را رفع کنید و دوباره فایل را بررسی کنید.",
    "Columns, units and ranges look right.": "ستون‌ها، واحدها و محدوده‌ها درست به نظر می‌رسند.",
    "valid": "معتبر", "error": "خطا", "check": "بررسی", "known": "موجود", "Saving…": "در حال ذخیره…",
    "Saved. It is now waiting for the next retraining.": "ذخیره شد و منتظر آموزش مجدد بعدی است.",
    "Saving needs a signed-in viewer with access to this page. You can still check batches here.": "ذخیره نیاز به ورود و دسترسی به این صفحه دارد. همچنان می‌توانید بچ‌ها را بررسی کنید.",
    "You can check batches, but saving needs edit access to this page.": "می‌توانید بچ‌ها را بررسی کنید، اما ذخیره نیاز به دسترسی ویرایش دارد.",
    "Batch log": "سیاههٔ بچ‌ها", "Batch": "بچ", "Recipe": "دستورالعمل", "Added": "افزوده‌شده", "Predicted with": "پیش‌بینی با مدل",
    "Status": "وضعیت", "No imported batches yet.": "هنوز بچی وارد نشده است.", "waiting for retrain": "در انتظار آموزش مجدد",
    "stored · model kept": "ذخیره شد · مدل قبلی حفظ شد", "in store": "در مخزن", "rejected": "رد شد",
    "Retraining runs automatically on GitHub. Upload a batch CSV to": "آموزش مجدد به‌طور خودکار روی GitHub انجام می‌شود. فایل CSV بچ را بارگذاری کنید در",
    "upload page": "صفحهٔ بارگذاری", "open upload page": "بازکردن صفحهٔ بارگذاری",
    ": the pipeline validates it, predicts it first, retrains, runs the promotion checks and republishes this site, usually within 5 minutes. The new model appears here as the next version.": ": خط لوله آن را اعتبارسنجی، پیشاپیش پیش‌بینی، آموزش مجدد و آزمون‌های ارتقا را اجرا می‌کند و این سایت را معمولاً ظرف ۵ دقیقه دوباره منتشر می‌کند. مدل جدید به‌عنوان نسخهٔ بعدی اینجا نمایش داده می‌شود.",
    "Saved batches can't be reached yet; the list may be incomplete.": "به بچ‌های ذخیره‌شده هنوز دسترسی نیست؛ فهرست ممکن است ناقص باشد.",
    // model view
    "Current model": "مدل فعلی", "Promotion checks for this version": "آزمون‌های ارتقای این نسخه", "Direction checks": "آزمون‌های جهت اثر",
    "Initial version: baseline for later checks": "نسخهٔ اولیه: مبنای آزمون‌های بعدی",
    "Version history": "تاریخچهٔ نسخه‌ها",
    "every new batch makes a candidate; it replaces the current model only if it passes the checks": "هر بچ جدید یک مدل نامزد می‌سازد؛ فقط در صورت قبولی در آزمون‌ها جایگزین مدل فعلی می‌شود",
    "Error by model version": "خطا بر حسب نسخهٔ مدل", "Titer error on benchmark": "خطای تیتر روی مجموعهٔ محک",
    "VCD error on benchmark": "خطای VCD روی مجموعهٔ محک", "Titer error of a new batch, predicted first": "خطای تیتر بچ جدید، پیش‌بینی پیشاپیش",
    "Version": "نسخه", "Created after": "ایجاد پس از", "In band": "درون بازه", "Decision": "تصمیم",
    "baseline": "مبنا", "promoted": "ارتقا یافت", "kept previous": "نسخهٔ قبلی حفظ شد", "initial build": "ساخت اولیه",
    "real data": "دادهٔ واقعی", "literature": "منابع علمی",
    "Measured data or prediction?": "دادهٔ اندازه‌گیری‌شده یا پیش‌بینی؟",
    "Every line and KPI on the Plan view is a model prediction, even for a recipe that was run for real. Measured values appear only as grey points and as “Measured” under a KPI. The table compares how much real replicates of the same recipe differ from each other (the limit set by the lab data) with how far the model is off (the error the model adds).": "هر خط و شاخص در نمای طراحی، پیش‌بینی مدل است، حتی برای دستورالعملی که واقعاً اجرا شده است. مقادیر اندازه‌گیری‌شده فقط به‌صورت نقطه‌های خاکستری و عبارت «اندازه‌گیری‌شده» زیر شاخص‌ها نمایش داده می‌شوند. جدول، اختلاف تکرارهای واقعی یک دستورالعمل با یکدیگر (حدی که داده‌های آزمایشگاه تعیین می‌کنند) را با خطای مدل (خطایی که مدل اضافه می‌کند) مقایسه می‌کند.",
    "Between real replicates": "بین تکرارهای واقعی", "Model error, known recipes": "خطای مدل، دستورالعمل‌های شناخته", "Model error, unseen recipe": "خطای مدل، دستورالعمل نادیده",
    "Replicate spread: typical absolute difference of one replicate from the mean of its recipe at the same sampling day (titer and cell density as % of the mean). Model error: mean error over all sampled days of the benchmark runs, predicted from day 0. Where the model error is well above the replicate spread, the model, not the measurement, limits accuracy.": "پراکندگی تکرارها: اختلاف مطلق معمول یک تکرار از میانگین دستورالعمل خود در همان روز نمونه‌برداری (تیتر و چگالی سلولی به‌صورت درصدی از میانگین). خطای مدل: میانگین خطا در همهٔ روزهای نمونه‌برداری کشت‌های محک، با پیش‌بینی از روز ۰. هرجا خطای مدل بسیار بیشتر از پراکندگی تکرارها باشد، محدودکنندهٔ دقت، مدل است نه اندازه‌گیری.",
    "How accurate is it?": "دقت آن چقدر است؟",
    "Six real runs are kept out of training for good. Each one is predicted from day 0 using only its inputs, the same way a plan is predicted.": "شش کشت واقعی برای همیشه از آموزش کنار گذاشته شده‌اند. هر کدام فقط با ورودی‌های خودش از روز ۰ پیش‌بینی می‌شود، درست مانند پیش‌بینی یک برنامه.",
    "Known recipes": "دستورالعمل‌های شناخته", "Unseen recipe HIP+": "دستورالعمل نادیدهٔ HIP+",
    "Titer error, all days": "خطای تیتر، همهٔ روزها", "Titer error, day 10": "خطای تیتر، روز ۱۰", "Viable cell density error": "خطای چگالی سلول زنده", "Glucose error": "خطای گلوکز",
    "Feeding, glucose and Gal+ effects come from real data. Temperature, pH and DO effects come from literature (and one CHO-T127 temperature pair and one low-DO run), so those days are marked as prior.": "اثرهای تغذیه، گلوکز و Gal+ از داده‌های واقعی می‌آیند. اثرهای دما، pH و DO از منابع علمی (و یک جفت دمایی CHO-T127 و یک کشت با DO پایین) می‌آیند، بنابراین آن روزها با برچسب «منابع علمی» مشخص می‌شوند.",
    "Agitation is not an input yet. More real runs narrow the bands and turn prior days into data days.": "هم‌زدن هنوز ورودی نیست. کشت‌های واقعی بیشتر بازه‌ها را باریک‌تر و روزهای مبتنی بر منابع را به روزهای مبتنی بر داده تبدیل می‌کنند.",
    "Prediction vs measured": "پیش‌بینی در برابر اندازه‌گیری", "Line: twin prediction from day 0. Points: measured values.": "خط: پیش‌بینی دوقلو از روز ۰. نقطه‌ها: مقادیر اندازه‌گیری‌شده.",
    // gates + checks (from the model registry)
    "All direction checks pass": "همهٔ آزمون‌های جهت اثر قبول شدند", "Band coverage between 60% and 95%": "پوشش بازه بین ۶۰٪ و ۹۵٪",
    "ML corrections stay moderate (median below x1.42)": "اصلاحات یادگیری ماشین معتدل می‌مانند (میانه کمتر از ×1.42)",
    "Few corrections hit the x0.5/x2 limit (below 25%)": "اصلاحات کمی به حد ×0.5/×2 می‌رسند (کمتر از ۲۵٪)",
    "Titer error not worse than the best version so far by more than 1.5 pt (stops slow drift)": "خطای تیتر بیش از ۱٫۵ واحد بدتر از بهترین نسخهٔ تاکنون نیست (مانع افت تدریجی)",
    "Titer error on benchmark not worse by more than 1.0 pt": "خطای تیتر روی محک بیش از ۱٫۰ واحد بدتر نشده",
    "VCD error on benchmark not worse by more than 2.0 pt": "خطای VCD روی محک بیش از ۲٫۰ واحد بدتر نشده",
    "Glucose target 4 vs 8 lowers final titer": "هدف گلوکز ۴ در برابر ۸ تیتر نهایی را کاهش می‌دهد",
    "Glucose target 4 vs 8 collapses the culture": "هدف گلوکز ۴ در برابر ۸ کشت را فرو می‌پاشد",
    "Gal+ extends viability under glucose limitation": "Gal+ زنده‌مانی را در کمبود گلوکز طولانی‌تر می‌کند",
    "Daily feeding gives lower titer than 48 h feeding": "خوراک‌دهی روزانه تیتر کمتری از خوراک‌دهی ۴۸ ساعته می‌دهد",
    "33 degC shift lowers peak VCD": "کاهش دما به 33 °C بیشینهٔ VCD را کم می‌کند", "33 degC shift extends viability": "کاهش دما به 33 °C زنده‌مانی را طولانی‌تر می‌کند",
    "DO held at 5% lowers peak VCD": "DO ثابت در ۵٪ بیشینهٔ VCD را کم می‌کند", "pH 7.3 raises peak lactate": "pH 7.3 بیشینهٔ لاکتات را افزایش می‌دهد",
    // accessibility labels
    "Sections": "بخش‌ها", "Edit inputs": "ویرایش ورودی‌ها", "Apply changes to": "اعمال تغییرات بر", "Previous day": "روز قبل", "Next day": "روز بعد",
    "Inputs per day (click a row to edit)": "ورودی‌های روزانه (برای ویرایش روی ردیف کلیک کنید)", "Basis": "پشتوانه", "Basis legend": "راهنمای پشتوانه",
    "Start of culture": "آغاز کشت", "Prediction": "پیش‌بینی", "Control pH": "کنترل pH", "Control dissolved oxygen": "کنترل اکسیژن محلول",
    "pH set-point": "نقطه‌تنظیم pH", "DO set-point": "نقطه‌تنظیم DO", "Batch CSV text": "متن CSV بچ", "Load an example batch": "بارگذاری بچ نمونه",
    "Check result": "نتیجهٔ بررسی", "Benchmark run": "کشت محک", "Measured data versus model error": "دادهٔ اندازه‌گیری‌شده در برابر خطای مدل",
    "Model accuracy": "دقت مدل", "Within real data: inputs inside the real runs": "در محدودهٔ داده‌های واقعی: ورودی‌ها درون کشت‌های واقعی",
    "Literature prior: temperature, pH or DO effect not covered by real runs": "بر پایهٔ منابع علمی: اثر دما، pH یا DO که کشت‌های واقعی پوشش نمی‌دهند",
    "Outside tested range: feed or glucose beyond the real runs": "خارج از محدودهٔ آزموده‌شده: خوراک یا گلوکز فراتر از کشت‌های واقعی",
    "Theme": "پوسته", "Language": "زبان", "Auto": "خودکار", "Light": "روشن", "Dark": "تیره",
    // validation messages
    "At least 4 samples are needed.": "دست‌کم ۴ نمونه لازم است.", "Some cells are not numbers.": "برخی خانه‌ها عدد نیستند.",
    "The first sample must be at 0 h (inoculation).": "نخستین نمونه باید در ساعت 0 (تلقیح) باشد.",
    "time_h must increase from row to row.": "time_h باید ردیف‌به‌ردیف افزایش یابد.", "VCD at 0 h is required.": "VCD در ساعت 0 الزامی است.",
    "Titer looks like g/L; the file expects mg/L.": "به نظر می‌رسد تیتر بر حسب g/L است؛ فایل mg/L می‌خواهد.",
    "Glucose above 15: check it is g/L, not mM.": "گلوکز بالای ۱۵: بررسی کنید g/L باشد نه mM.", "Lactate above 5: check it is g/L, not mM.": "لاکتات بالای ۵: بررسی کنید g/L باشد نه mM.",
    "feed_pct above 15% v/v.": "feed_pct بیش از 15% v/v.", "Temperature outside 28–39 °C.": "دما خارج از 28 تا 39 °C.",
    "Feed above 5% v/v is outside the range the model was trained on.": "خوراک بیش از 5% v/v خارج از محدودهٔ آموزش مدل است.",
    "A glucose target outside 2–8 g/L is outside the trained range.": "هدف گلوکز خارج از 2 تا 8 g/L خارج از محدودهٔ آموزش است.",
    "Temperature differs from 37 °C: the model uses a literature prior there.": "دما با 37 °C متفاوت است: مدل در آنجا از منابع علمی استفاده می‌کند.",
    "pH outside 6.0–8.0.": "pH خارج از 6.0 تا 8.0.", "DO outside 0–200 % air saturation.": "DO خارج از 0 تا 200 % اشباع هوا.",
    "pH given: its effect comes from literature priors (no varied-pH runs yet).": "pH داده شده: اثر آن از منابع علمی می‌آید (هنوز کشتی با pH متغیر نیست).",
    "DO given: its effect comes from literature priors and one real low-DO run.": "DO داده شده: اثر آن از منابع علمی و یک کشت واقعی با DO پایین می‌آید.",
    "Agitation is stored for future models but not used yet.": "هم‌زدن برای مدل‌های آینده ذخیره می‌شود اما هنوز استفاده نمی‌شود.",
    "Initial build (v0.8 hybrid).": "ساخت اولیه (مدل ترکیبی v0.8)."
  };
  const RULES = [
    [/^Remove (.+)$/, "حذف $1"], [/^(.+) \(input\)$/, "$1 (ورودی)"], [/^Inputs, day (\d+)$/, "ورودی‌ها، روز $1"], [/^measured ([\d.]+)$/, "اندازه‌گیری‌شده $1"],
    [/^Combined chart: (.+) over culture days$/, "نمودار ترکیبی: $1 در طول روزهای کشت"],
    [/^Option (\d+)$/, "گزینهٔ $1"], [/^glucose to ([\d.]+) g\/L$/, "گلوکز تا $1 g/L"], [/^([\d.]+) °C from day (\d+)$/, "$1 °C از روز $2"],
    [/^vs current plan$/, "نسبت به برنامهٔ فعلی"], [/^([+-]?\d+)% vs current plan$/, "$1٪ نسبت به برنامهٔ فعلی"],
    [/^Final viability (\d+)% ·$/, "زنده‌مانی نهایی $1٪ ·"],
    [/^growth ×([\d.]+) \(1\.00 = typical NISTCHO run\), forecast restarts from the day-(\d+) measurements\.$/, "رشد ×$1 (1.00 = کشت معمول NISTCHO)؛ پیش‌بینی از اندازه‌گیری‌های روز $2 از نو آغاز می‌شود."],
    [/^Fit to days 0–(\d+): titer (\S+) , VCD (\S+) error\. (.*)$/, "برازش روزهای 0 تا $1: خطای تیتر $2، VCD $3."],
    [/^Fit to days 0–(\d+): titer (\S+), VCD (\S+) error\. Back-test on 6 held-out runs: titer error for the remaining days fell from 13\.7% to 7\.6% with data to day 5\.$/, "برازش روزهای 0 تا $1: خطای تیتر $2، خطای VCD $3. آزمون گذشته‌نگر روی ۶ کشت کنارگذاشته: با داده تا روز ۵، خطای تیتر روزهای باقی‌مانده از 13.7% به 7.6% کاهش یافت."],
    [/^Example: measured values of real run (\S+) \(recipe (\S+)\), days 0–(\d+)\. Replace them with your own\.$/, "نمونه: مقادیر اندازه‌گیری‌شدهٔ کشت واقعی $1 (دستورالعمل $2)، روزهای 0 تا $3. آن‌ها را با داده‌های خود جایگزین کنید."],
    [/^Pasted data: (\d+) samples, days 0–(\d+)\.$/, "دادهٔ چسبانده‌شده: $1 نمونه، روزهای 0 تا $2."],
    [/^Days 0–(\d+) measured · (\d+) of (\d+) remaining days within real data$/, "روزهای 0 تا $1 اندازه‌گیری‌شده · $2 از $3 روز باقی‌مانده در محدودهٔ داده‌های واقعی"],
    [/^Days 0–(\d+) measured ·$/, "روزهای 0 تا $1 اندازه‌گیری‌شده ·"], [/^(\d+) of (\d+) remaining days within real data$/, "$1 از $2 روز باقی‌مانده در محدودهٔ داده‌های واقعی"],
    [/^No combination keeps final viability at or above (\d+)%\. Lower the limit or check the measured data\.$/, "هیچ ترکیبی زنده‌مانی نهایی را در $1٪ یا بالاتر نگه نمی‌دارد. حد را پایین بیاورید یا داده‌ها را بررسی کنید."],
    [/^(\S+) day (\d+)$/, "$1 روز $2"],
    [/^Day (\d+)$/, "روز $1"], [/^day (\d+)$/, "روز $1"], [/^Day (\d+) only$/, "فقط روز $1"], [/^Day (\d+) onward$/, "از روز $1 به بعد"],
    [/^Changes apply from day (\d+) to day (\d+)\. .*$/, "تغییرات از روز $1 تا روز $2 اعمال می‌شوند. خوراک، گلوکز و Gal+ فقط در روزهای دارای خوراک تغییر می‌کنند؛ دما، pH و DO در همهٔ روزها."],
    [/^Changes apply to day (\d+) only\.$/, "تغییرات فقط بر روز $1 اعمال می‌شوند."],
    [/^(\d+) of (\d+) days within real data$/, "$1 روز از $2 روز در محدودهٔ داده‌های واقعی"], [/^All (\d+) days within real data$/, "هر $1 روز در محدودهٔ داده‌های واقعی"],
    [/^(\d+) days? use a literature prior$/, "$1 روز بر پایهٔ منابع علمی"], [/^(\d+) days? outside tested range$/, "$1 روز خارج از محدودهٔ آزموده‌شده"],
    [/^80% range (.+?)( ·)?$/, (m, a, b) => "بازهٔ ۸۰٪ " + a + (b ? " ·" : "")],
    [/^IVCD (\S+) 10⁶ cell·d\/mL$/, "\u2066IVCD $1 10⁶ cell·d/mL\u2069"],
    [/^Measured · (\d+) real runs of (.+)$/, "اندازه‌گیری‌شده · $1 کشت واقعی $2"],
    [/^\((\d+) real runs?, day (\d+)\+\)$/, "($1 کشت واقعی، روز $2 به بعد)"], [/^\((\d+) real runs?\)$/, "($1 کشت واقعی)"],
    [/^▲ above (\S+) off scale ·$/, "▲ بالاتر از $1 خارج از مقیاس ·"], [/^model error ±(.+?) ·$/, (m, a) => "خطای مدل ±" + a.replace("pts", "امتیاز") + " ·"],
    [/^benchmark typical (.+)$/, "معمول در محک $1"], [/^(\d+) of (\d+) measurements$/, "$1 از $2 اندازه‌گیری"],
    [/^(\d+) real runs in store · (\d+) imported$/, "$1 کشت واقعی در مخزن · $2 واردشده"], [/^(\d+) benchmark runs$/, "$1 کشت محک"], [/^(\d+) runs$/, "$1 کشت"],
    [/^Model ([\d.]+)$/, "مدل $1"], [/^in model ([\d.]+)$/, "در مدل $1"], [/^since (.+)$/, "از $1"],
    [/^Model ([\d.]+) · mechanistic mass balances with machine-learned rate corrections · (\d+) real runs in store \((\d+) kept out for benchmarking\) · .*$/,
      "مدل $1 · موازنهٔ جرم مکانیستی با اصلاح نرخ‌ها به کمک یادگیری ماشین · $2 کشت واقعی در مخزن ($3 کشت برای محک کنار گذاشته شده) · پیش‌بینی‌ها مبتنی بر مدل‌اند و پشتوانهٔ هرکدام مشخص است."],
    [/^(.+) · unseen recipe$/, "$1 · دستورالعمل نادیده"], [/^(.+) · known recipe$/, "$1 · دستورالعمل شناخته"], [/^(.+) \(real run\)$/, "$1 (کشت واقعی)"],
    [/^(.+) · refit$/, "$1 · برازش مجدد"],
    [/^recipe (\S+) · (\d+) samples · to day (.+)$/, "دستورالعمل $1 · $2 نمونه · تا روز $3"], [/^(\d+) samples · to day (.+)$/, "$1 نمونه · تا روز $2"],
    [/^Trained on (\d+) real runs and (\d+) derived runs\. Created after batch (.+?), with a mechanistic refit\.$/, "آموزش‌دیده روی $1 کشت واقعی و $2 کشت مشتق‌شده. ایجادشده پس از بچ $3، با برازش مجدد مکانیستی."],
    [/^Trained on (\d+) real runs and (\d+) derived runs\. Created after batch (.+?), ML corrections retrained\.$/, "آموزش‌دیده روی $1 کشت واقعی و $2 کشت مشتق‌شده. ایجادشده پس از بچ $3، با آموزش مجدد اصلاحات یادگیری ماشین."],
    [/^Trained on (\d+) real runs and (\d+) derived runs\. Initial build \(v0\.8 hybrid\)\.$/, "آموزش‌دیده روی $1 کشت واقعی و $2 کشت مشتق‌شده. ساخت اولیه (مدل ترکیبی v0.8)."],
    [/^Trained on (\d+) real NISTCHO runs plus (\d+) runs derived from replicate variation \(v0\.7\)\. Base data: 7 feeding strategies, Schaepertoens et al\. 2026\.$/,
      "آموزش‌دیده روی $1 کشت واقعی NISTCHO به‌علاوهٔ $2 کشت مشتق‌شده از تغییرپذیری تکرارها (v0.7). دادهٔ پایه: ۷ راهبرد تغذیه، Schaepertoens و همکاران ۲۰۲۶."],
    [/^(.+) is already in the model's run store\. You can still see how the model predicts it\.$/, "$1 از قبل در مخزن کشت‌های مدل است. همچنان می‌توانید پیش‌بینی مدل را برای آن ببینید."],
    [/^(.+) is already saved and waiting for retraining\. You can still see how the model predicts it\.$/, "$1 از قبل ذخیره شده و منتظر آموزش مجدد است. همچنان می‌توانید پیش‌بینی مدل را ببینید."],
    [/^([+-]\d+)% vs (.+)$/, "$1٪ نسبت به $2"], [/^± ?([\d.]+) pts$/, "±$1 امتیاز"], [/^±([\d.]+)$/, "±$1"],
    [/^([\d.]+%) \(best ([\d.]+%)\)$/, "$1 (بهترین $2)"], [/^([\d.]+%) \(current ([\d.]+%)\)$/, "$1 (فعلی $2)"],
    [/^Missing columns: (.+)$/, "ستون‌های گم‌شده: $1"], [/^missing columns: (.+)$/, "ستون‌های گم‌شده: $1"],
    [/^(\S+) outside (\S+)–(\S+): (\d+) value\(s\)\.$/, "$1 خارج از $2 تا $3: $4 مقدار."],
    [/^Fewer than 3 (\S+) measurements: little to learn from\.$/, "کمتر از ۳ اندازه‌گیری $1: دادهٔ کمی برای یادگیری."],
    [/^Downloaded (.+)\. Upload it to$/, "$1 دانلود شد. آن را بارگذاری کنید در"],
    [/^; the site retrains and updates in a few minutes\.$/, "؛ سایت ظرف چند دقیقه آموزش مجدد و به‌روزرسانی می‌شود."],
    [/^(\d+) batch(?:es)? waiting\.$/, "$1 بچ در انتظار."],
    [/^Could not save: (.+)\. Try again\.$/, "ذخیره نشد: $1. دوباره تلاش کنید."]
  ];
  function tr(s) {
    const core = s.trim(); if (!core) return s;
    let out = EX[core];
    if (out == null) for (const [re, rep] of RULES) { if (re.test(core)) { out = core.replace(re, rep); break; } }
    if (out == null) {   // bare numbers and ranges ("82–84", "1.89–2.04"): keep them left-to-right inside Persian text
      return /^[\d.,\s–\-%±]+$/.test(core) && /\d/.test(core) ? s.replace(core, "\u2066" + core + "\u2069") : s;
    }
    // keep number ranges and value+unit groups left-to-right inside Persian text (e.g. "1.64–2.17", "10⁶ cells/mL")
    out = out.replace(/(\d[\d.,]*\s?[–-]\s?\d[\d.,]*\s?%?|±\s?\d[\d.]*\s?(?:g\/L|%)?|\d[\d.]*\s?(?:g\/L|mg\/L|%\s?v\/v|°C)|10⁶ [A-Za-z·\/]+)/g, "\u2066$1\u2069");
    const lead = s.match(/^\s*/)[0], trail = s.match(/\s*$/)[0];
    return lead + out + trail;
  }
  // ---- applying it to the page
  let lang = "en", busy = false;
  const orig = new WeakMap();        // text node -> { en, fa }
  const SKIP = new Set(["SCRIPT", "STYLE", "CODE", "PRE", "TEXTAREA"]);
  const ATTRS = ["aria-label", "placeholder", "title"];
  function pass() {
    busy = true;
    const w = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
    let n;
    while ((n = w.nextNode())) {
      const p = n.parentElement; if (!p || SKIP.has(p.tagName) || p.closest("code,pre,[data-notr]")) continue;
      let rec = orig.get(n);
      if (!rec || (n.nodeValue !== rec.fa && n.nodeValue !== rec.en)) { rec = { en: n.nodeValue, fa: tr(n.nodeValue) }; orig.set(n, rec); }
      const want = lang === "fa" ? rec.fa : rec.en; if (n.nodeValue !== want) n.nodeValue = want;
    }
    document.querySelectorAll("[aria-label],[placeholder],[title]").forEach(el => ATTRS.forEach(a => {
      if (!el.hasAttribute(a)) return;
      const key = "data-en-" + a, cur = el.getAttribute(a);
      let en = el.getAttribute(key);
      if (en == null || (cur !== en && cur !== tr(en))) { en = cur; el.setAttribute(key, en); }
      const want = lang === "fa" ? tr(en) : en; if (cur !== want) el.setAttribute(a, want);
    }));
    busy = false;
  }
  let queued = false;
  const obs = new MutationObserver(() => { if (busy || queued) return; queued = true; requestAnimationFrame(() => { queued = false; pass(); }); });
  function setLang(l) {
    lang = l === "fa" ? "fa" : "en";
    document.documentElement.lang = lang; document.documentElement.dir = lang === "fa" ? "rtl" : "ltr";
    document.title = lang === "fa" ? EX["CHO Fed-Batch Twin"] : "CHO Fed-Batch Twin";
    pass();
  }
  function start() { obs.observe(document.body, { childList: true, subtree: true, characterData: true }); }
  root.I18N = { setLang, start, tr, get lang() { return lang; } };
})(window);
