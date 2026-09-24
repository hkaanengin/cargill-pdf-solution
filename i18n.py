"""Turkish by default, English on a switch (R31).

Every string the app shows is written in English in the templates and
`app.py`, and passed through `translate()`. For Turkish it is looked up in
`TR` below, keyed by that English text. Placeholders in `{braces}` are filled
after the lookup, so the Turkish sentence can put them wherever Turkish word
order wants them.

Per-file reasons are keyed by `Problem` instead (`REASONS_TR`). The English
reason is `Outcome.message` from `stamper.py`, and the Turkish one is built
from `Outcome.details`, the values that message was made from.

Data is never translated: file names, POs, sheet names (`FATURA`, `DEKONT`),
column headers and the `PO:` stamp stay as they are.

**Reviewing:** the Turkish below is a draft by Claude, and R31 is not done
until the user has reviewed it. Edit the right-hand side only. The English key
must match the template exactly. `tests/test_i18n.py` fails if a string the
templates use has no entry here.

See vault/decisions/0016-translations-as-a-dict.md.
"""

from stamper import Problem

LANGUAGES = ("tr", "en")
DEFAULT_LANGUAGE = "tr"

TR: dict[str, str] = {
    # --- Shell: base.html -------------------------------------------------
    "PO Stamper": "PO Stamper",
    "Progress": "İlerleme",
    "Language": "Dil",
    "Workbook": "Excel dosyası",
    "PDFs": "PDF'ler",
    "Results": "Sonuçlar",

    # --- Step 1: excel.html -----------------------------------------------
    "What it needs": "Gerekenler",
    "sheet 2": "2. sayfa",
    "sheet 3": "3. sayfa",
    "columns": "sütunlar",
    "PO numbers are looked up here. It stays in memory for this session and is never saved.":
        "PO numaraları bu dosyadan bulunur. Dosya yalnızca bu oturum boyunca "
        "bellekte tutulur, hiçbir yere kaydedilmez.",
    "Drop the Excel workbook, or browse": "Excel dosyasını buraya bırakın veya seçin",
    ".xlsx or .xlsm": ".xlsx veya .xlsm",
    "Load workbook": "Dosyayı yükle",
    "Loaded": "Yüklü",
    "Continue to PDFs": "PDF'lere geç",
    "To use a different workbook, load it below.":
        "Başka bir Excel dosyası kullanmak için aşağıdan yükleyin.",
    "This clears the results of the last run.": "Bu işlem son işlemin sonuçlarını siler.",
    "Load a different workbook": "Başka bir Excel dosyası yükle",
    "Loading…": "Yükleniyor…",

    # --- Step 2: stamp.html -----------------------------------------------
    "entries": "kayıt",
    "Replace workbook": "Excel dosyasını değiştir",
    "Last run: {n} of {total} stamped": "Son işlem: {total} dosyadan {n} tanesi damgalandı",
    "Queue": "Damgalanacak dosyalar",
    "Each file name is matched against the workbook and its PO is stamped on page 1.":
        "Her dosyanın adı Excel dosyasında aranır ve bulunan PO numarası ilk "
        "sayfaya basılır.",
    "Stamp": "Damgala",
    "Drop PDFs, or browse": "PDF dosyalarını buraya bırakın veya seçin",
    "SGM… and SUB… go to FATURA · digits-only go to DEKONT":
        "SGM… ve SUB… ile başlayanlar FATURA sayfasında, yalnızca rakamdan "
        "oluşanlar DEKONT sayfasında aranır",
    "Selected files": "Seçilen dosyalar",
    "No files selected": "Dosya seçilmedi",
    "Chosen files appear here before you stamp them.":
        "Seçtiğiniz dosyalar damgalanmadan önce burada listelenir.",
    "{n} file": "{n} dosya",
    "{n} files": "{n} dosya",
    "Stamp {n} file": "{n} dosyayı damgala",
    "Stamp {n} files": "{n} dosyayı damgala",
    "Stamping…": "Damgalanıyor…",
    "Remove {name}": "{name} dosyasını listeden çıkar",
    "Already in the list, so not added again: {names}":
        "Zaten listede olduğu için tekrar eklenmedi: {names}",

    # --- Step 3: result.html ----------------------------------------------
    "Stamped {n} of {total} file": "{total} dosyadan {n} tanesi damgalandı",
    "Stamped {n} of {total} files": "{total} dosyadan {n} tanesi damgalandı",
    "/ {total} stamped": "/ {total} damgalandı",
    "Download zip": "Zip indir",
    "Download PDF": "PDF indir",
    "Nothing was stamped, so there is nothing to download. Every file is listed below with the reason.":
        "Hiçbir dosya damgalanmadı, bu yüzden indirilecek bir şey yok. Her "
        "dosya, nedeniyle birlikte aşağıda listelenmiştir.",
    "Stamp more PDFs": "Başka PDF damgala",
    "Use a different workbook": "Başka bir Excel dosyası kullan",
    # Group headings (R21), one per `Problem`, plus the stamped group.
    "Stamped": "Damgalandı",
    "Not stamped: key not in the workbook": "Damgalanmadı: Excel dosyasında bulunamadı",
    "Not stamped: row found, but PO is blank": "Damgalanmadı: satır bulundu ama PO boş",
    "Not stamped: file name matches no known pattern":
        "Damgalanmadı: dosya adı tanınan bir biçimde değil",
    "Not stamped: key is on more than one workbook row":
        "Damgalanmadı: Excel dosyasında birden fazla satırda var",
    "Not stamped: already carries a PO stamp": "Damgalanmadı: zaten PO damgası var",
    "Withheld: stamp could not be verified": "Verilmedi: damga doğrulanamadı",
    "Not stamped: uploaded more than once": "Damgalanmadı: birden fazla kez yüklendi",
    "Ignored: not a PDF": "Yok sayıldı: PDF değil",

    # --- Flash messages: app.py -------------------------------------------
    "Please choose an Excel file.": "Lütfen bir Excel dosyası seçin.",
    "Please upload an Excel workbook (.xlsx).": "Lütfen bir Excel dosyası (.xlsx) yükleyin.",
    "Could not read that workbook: {error}": "Bu Excel dosyası okunamadı: {error}",
    "Loaded {n} entries from “{name}”.": "“{name}” dosyasından {n} kayıt yüklendi.",
    "Upload the Excel source first.": "Önce Excel dosyasını yükleyin.",
    "Please choose at least one PDF file.": "Lütfen en az bir PDF dosyası seçin.",
    "That download is no longer available — upload the PDFs again.":
        "Bu indirme artık mevcut değil — PDF dosyalarını yeniden yükleyin.",
    "That upload is over the {limit} MB limit. Send the PDFs in smaller batches.":
        "Yükleme {limit} MB sınırını aşıyor. PDF dosyalarını daha küçük "
        "gruplar halinde gönderin.",
}

# Each file's reason for not being stamped, shown after its name on the
# results page: "917031.pdf — <reason>". Lower case, no final stop, like the
# English in `stamper.py`. Placeholders come from `Outcome.details`.
REASONS_TR: dict[Problem, str] = {
    Problem.UNROUTABLE:
        "dosya adı SGM… veya SUB… ile başlamıyor ve yalnızca rakamlardan "
        "oluşmuyor, bu yüzden hangi sayfada aranacağı belirlenemedi",
    Problem.NOT_IN_WORKBOOK: "yüklenen Excel dosyasının {sheet} sayfasında yok",
    Problem.DUPLICATE_KEY:
        "{sheet} sayfasında {rows} satırda geçiyor — bu, Excel dosyasındaki "
        "bir veri girişi hatası; düzeltme PDF'te değil, Excel dosyasında yapılmalı",
    Problem.PO_BLANK: "{sheet} sayfasında bulundu ama PO hücresi boş",
    Problem.ALREADY_STAMPED:
        "zaten bir PO: damgası taşıyor, bu yüzden ikinci kez damgalanmadı",
    Problem.STAMP_NOT_VERIFIED:
        "damgalandı ama {stamp} ifadesi sonrasında 1. sayfada bulunamadı, bu "
        "yüzden dosya verilmedi",
    Problem.REPEATED_UPLOAD:
        "bu işlemde birden fazla kez yüklendi; ilk kopya işlendi, bu kopya işlenmedi",
    Problem.NOT_A_PDF: "PDF değil, bu yüzden yok sayıldı",
}


def translate(text: str, lang: str, **params) -> str:
    """`text` in `lang`, with `{placeholders}` filled from `params`.

    A string with no Turkish entry falls back to the English rather than
    failing a request. `tests/test_i18n.py` is what keeps that from happening.
    """
    if lang == "tr":
        text = TR.get(text, text)
    return text.format(**params) if params else text


def reason(outcome, lang: str) -> str:
    """One file's reason for not being stamped, in `lang`."""
    if lang == "tr" and outcome.problem in REASONS_TR:
        try:
            return REASONS_TR[outcome.problem].format(**(outcome.details or {}))
        except (KeyError, IndexError):
            pass  # a detail missing: the English below is still true
    return outcome.message
