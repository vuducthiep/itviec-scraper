# ITviec Scraper + SQLite + Streamlit Dashboard

Du an nay dung Playwright + Cheerio de crawl job tu ITviec, luu ket qua ra JSON, import vao SQLite, sau do hien thi dashboard bang Streamlit.

## Yeu cau

- Node.js 18+
- Python 3.10+
- Chromium cho Playwright

## 1. Cai dependencies

Cai package Node.js:

```bash
npm install
npx playwright install chromium
```

Cai package Python cho Streamlit:

```bash
pip install -r requirements.txt
```

## 2. Them cookie dang nhap ITviec

Neu khong co cookie dang nhap, salary co the hien la `"Sign in to view salary"`. De lay salary that:

1. Dang nhap `itviec.com` tren Chrome.
2. Mo DevTools -> tab Network.
3. Click mot request bat ky toi `itviec.com`.
4. Trong Request Headers, copy gia tri cua header `Cookie`.
5. Tao file `cookies-raw.txt` va paste cookie vao do.
6. Chay:

```bash
node build-cookies.js
```

Lenh nay tao file `itviec-cookies.json`. Scraper se tu load file nay khi chay.

Luu y: `cookies-raw.txt` va `itviec-cookies.json` chua session dang nhap, khong commit va khong chia se cho nguoi khac.

## 3. Chay scraper

```bash
node scraper.js
```

Scraper co resume. Neu bi tat giua chung, chi can chay lai lenh tren, no se doc tiep tu `itviec-state.json`.

File quan trong:

- `itviec-state.json`: checkpoint trong luc dang crawl.
- `itviec-jobs.json`: output cuoi cung sau khi crawl xong.
- `itviec-cookies.json`: cookie Playwright storage state.

Luu y: `itviec-jobs.json` chi duoc ghi khi scraper chay xong phase detail va state thanh `"done"`. Neu dang crawl ma file nay rong thi binh thuong, xem tien do trong `itviec-state.json`.

Muon crawl lai tu dau:

```bash
del itviec-state.json
node scraper.js
```

Tren macOS/Linux:

```bash
rm itviec-state.json
node scraper.js
```

## 4. Lam sach du lieu

Sau khi scraper co du lieu, co the tao ban JSON da chuan hoa:

```bash
python clean_jobs.py
```

Lenh nay tao file:

```text
itviec-jobs-clean.json
```

File clean se trim text, dedupe tags/skills, chuan hoa `location`, `workingMode`, `label`, va them `salaryMinUsd` / `salaryMaxUsd` neu parse duoc salary.

Neu khong can clean rieng, co the bo qua buoc nay va import truc tiep tu `itviec-jobs.json`.

## 5. Import du lieu vao SQLite

Sau khi co du lieu, chay:

```bash
python import_to_sqlite.py
```

Lenh nay tao file:

```text
itviec.db
```

Script import se uu tien doc `itviec-jobs.json`. Neu file JSON cuoi chua co nhung `itviec-state.json` da co du lieu tam, script van co the import du lieu hien co tu state.

Neu muon import tu file da clean:

```bash
python import_to_sqlite.py --json itviec-jobs-clean.json
```

SQLite gom 2 bang chinh:

- `jobs`: thong tin job.
- `job_skills`: quan he job va skill de thong ke skill de hon.

## 6. Chay Streamlit dashboard

```bash
streamlit run streamlit_app.py
```

Streamlit se in ra URL, thuong la:

```text
http://localhost:8501
```

Dashboard hien co:

- Tong so jobs, companies, locations, skills.
- Filter theo keyword, location, working mode.
- Loc job co salary.
- Chart top skills.
- Chart working mode.
- Bang danh sach jobs.
- Xem chi tiet job.

## Flow day du

Chay tu dau den cuoi:

```bash
npm install
npx playwright install chromium
pip install -r requirements.txt
node build-cookies.js
node scraper.js
python clean_jobs.py
python import_to_sqlite.py --json itviec-jobs-clean.json
streamlit run streamlit_app.py
```

Neu khong can buoc clean:

```bash
node scraper.js
python import_to_sqlite.py
streamlit run streamlit_app.py
```

Neu da co cookie va dependencies roi, moi lan cap nhat du lieu nen chay:

```bash
node scraper.js
python clean_jobs.py
python import_to_sqlite.py --json itviec-jobs-clean.json
streamlit run streamlit_app.py
```

## Cau hinh scraper

Sua trong `scraper.js`, object `CONFIG`:

| Key | Y nghia |
|---|---|
| `baseUrl` | URL list jobs ITviec |
| `maxPages` | `null` la crawl tat ca, hoac dat so page toi da |
| `outputFile` | File JSON output cuoi |
| `cookiesFile` | File cookie Playwright |
| `stateFile` | File checkpoint resume |
| `headless` | `true` chay an browser, `false` de xem browser khi debug |
| `detailConcurrency` | So detail page crawl song song |
| `saveEvery` | So job detail moi lan save state |

## Bao mat va gitignore

Khong commit cac file du lieu va session:

- `cookies-raw.txt`
- `itviec-cookies.json`
- `itviec-state.json`
- `itviec-jobs.json`
- `itviec-jobs-clean.json`
- `itviec.db`

Nhung file nay da duoc dua vao `.gitignore`.

## Troubleshooting

Neu `itviec-jobs.json` rong:

- Kiem tra `itviec-state.json`.
- Neu `"phase": "list"` hoac `"phase": "detail"` thi scraper chua xong.
- Chay tiep `node scraper.js`.

Neu salary van la `"Sign in to view salary"`:

- Cookie co the het han.
- Copy lai Cookie tu Chrome sau khi dang nhap ITviec.
- Chay lai `node build-cookies.js`.
- Chay lai `node scraper.js`.

Neu gap Cloudflare lien tuc:

- Thu giam `detailConcurrency` trong `scraper.js` xuong `1` hoac `2`.
- Dam bao `cf_clearance` trong cookie con moi.

## File chinh

| File | Muc dich |
|---|---|
| `scraper.js` | Crawl ITviec va ghi JSON/state |
| `build-cookies.js` | Convert raw Cookie header sang Playwright storageState |
| `clean_jobs.py` | Chuan hoa du lieu crawl ra `itviec-jobs-clean.json` |
| `import_to_sqlite.py` | Import JSON/state vao SQLite |
| `streamlit_app.py` | Dashboard Streamlit |
| `requirements.txt` | Python dependencies |
| `dashboard.html` | Dashboard HTML cu cua repo |

## License

Chi dung cho muc dich hoc tap va phan tich du lieu ca nhan. Hay tuan thu dieu khoan su dung cua ITviec.
