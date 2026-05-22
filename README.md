# Vault Automation Kit (Release)

This is an automation toolkit for Obsidian Vaults.  
The release version is designed for public use and can be customized through a config file (folders, classification rules, AI settings, and backup behavior).

## What Can This Do?

1. Automatically classify and move notes from `_Inbox`  
Destination folders are configurable in `config.yml`. The default release categories are methods, experiments, terms, writing, and book reading.

2. Automatically insert Wiki links into note bodies  
Links are generated from your dictionary file and existing note names.

3. Generate weekly and monthly summaries (when OpenAI is enabled)  
Weekly summaries use Daily Notes. Monthly summaries use weekly summaries. They are generated only when the current date matches `summary.weekly_weekday` or `summary.monthly_day` in `config.yml`.

4. Create Git backups on `--apply`  
Changes are committed and optionally pushed to your remote.

## What To Do After Downloading

1. Install dependencies

```bash
cd release
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

2. Create a config file

```bash
cp config.example.yml config.yml
```

3. Edit `config.yml`
- Set `vault_root` to the absolute path of your vault
- Adjust category folders and keywords if needed
- Adjust `summary.weekly_weekday` and `summary.monthly_day` if you use summaries
- If you want Git push, check `git_backup.push: true` and `git_backup.remote`

4. Set your OpenAI API key (if using AI features)

You can either export it in your shell, or keep it in a local `.env` file that is not committed.

```bash
cp .env.example .env
# then edit .env
```

5. Run a dry-run first

```bash
./maintain
# or: python scripts/pipeline.py --dry-run --config config.yml
```

6. Apply changes

```bash
./maintain apply
# or: python scripts/pipeline.py --apply --config config.yml
```

## Execution Modes

- `./maintain` or `--dry-run`: Preview planned changes only (no file modifications)
- `./maintain apply` or `--apply`: Execute moves, link insertion, summary generation, and Git backup

## Default Folders

The release defaults in `config.example.yml` are:

- `_Inbox`: Unsorted input notes and files
- `_Inbox/needs_review`: Files that could not be classified confidently
- `_attachments`: PDFs and images
- `00_DailyNote`: Daily Notes used for weekly summaries
- `10_Research/00_Methods`: Methods, models, implementations, and architecture notes
- `10_Research/10_Experiments`: Experiment logs, results, and evaluations
- `10_Research/20_Terms`: Terms, definitions, concepts, and metrics
- `10_Research/30_Writing`: Paper drafts, presentations, and reports
- `20_BookReading`: Book notes
- `10_Research/40_Progress/weekly_summaries`: Weekly summaries
- `10_Research/40_Progress/monthly_summaries`: Monthly summaries

## Can I Use This Without OpenAI?

Yes.  
Set `ai.enabled: false` in `config.yml` to run rule-based automation only. AI-based classification and weekly/monthly summary generation will be skipped without `OPENAI_API_KEY`.

## Structure

- `maintain`: Short wrapper for the main pipeline
- `scripts/pipeline.py`: Main execution entrypoint
- `scripts/config_ops.py`: Config loading and directory setup
- `scripts/classify_ops.py`: Inbox classification and file moves
- `scripts/link_ops.py`: Wiki link insertion
- `scripts/summary_ops.py`: Weekly/monthly summary generation
- `scripts/backup_ops.py`: Git backup logic
- `scripts/lib_automation.py`: Compatibility shim for older imports
- `config.example.yml`: Configuration template

`*_ops.py` uses `ops` as short for `operations`.  
Each file contains one functional unit of the pipeline.

## Notes

- This release is a standalone, public-friendly version separated from `Vault/scripts`.
- Always validate behavior with `--dry-run` before using `--apply`.

