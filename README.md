
# 🔍 Django Index Optimizer

**Django Index Optimizer** is a plug-and-play Django management command that analyzes your PostgreSQL query statistics and recommends indexes based on actual query patterns. It's designed to help **beginners and early-stage developers** optimize their applications **before scaling**, with minimal setup.

---

## 🚀 Features

- 📊 Analyzes `pg_stat_statements` to find slow or frequent queries.
- 🧠 Extracts filter patterns (`WHERE`, `ORDER BY`, `GROUP BY`) to identify indexing opportunities.
- 💡 Recommends relevant single-column indexes.
- ⚙️ Optionally creates missing indexes automatically.
- 🔁 Can be run regularly or manually via `manage.py`.

---

## 📦 Installation

1. **Install the package:**

```bash
pip install django-index-optimizer
```

2. **Add it to your Django project:**

```python
# settings.py

INSTALLED_APPS = [
    ...
    "optimizer",
]
```

3. **Ensure PostgreSQL has `pg_stat_statements` enabled:**

Add this to your `postgresql.conf` (or via cloud provider settings):

```conf
shared_preload_libraries = 'pg_stat_statements'
```

Then restart PostgreSQL and run:

```sql
CREATE EXTENSION IF NOT EXISTS pg_stat_statements;
```

---

## ⚡ Usage

Once installed, you can run the management command to optimize your indexes:

```bash
python manage.py optimize_indexes
```

This will:

1. Fetch frequent or slow queries from `pg_stat_statements`.
2. Analyze which columns are used most often in queries.
3. Recommend indexes and attempt to create them (using `CREATE INDEX CONCURRENTLY`).

---

## 📁 Project Structure

```
optimizer/
├── __init__.py
├── analyzer.py         # Fetches and parses query stats
├── recommender.py      # Suggests columns to index
├── applier.py          # Applies indexes if needed
└── management/
    └── commands/
        └── optimize_indexes.py   # Main management command file
```

---

## 🤝 Contributing

Contributions are welcome and **encouraged** — especially from beginners!

Whether it's:
- Improving index detection
- Supporting multi-column indexes
- Adding tests or docs
- Reporting bugs or edge cases

You're welcome to open issues or submit pull requests.

### 🛠 To develop locally:

```bash
git clone https://github.com/yassinbahri/django-index-optimizer.git
cd django-index-optimizer
pip install -e .
```

Then, add `"optimizer"` to a Django project and run tests or the management command.

---

## 📃 License

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for details.

---

## 🙌 A Note to Beginners

This tool was built with **you** in mind. Indexing is a powerful and often overlooked step in web app performance — by learning it early, you’ll save yourself many headaches down the line. 💡

Happy optimizing!