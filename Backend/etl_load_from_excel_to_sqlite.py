import os
import re
import sys
import sqlite3
import pandas as pd
from typing import Dict, Tuple

# Input Excel file and output SQLite database
EXCEL_FILE = 'dummy_data.xlsx'
SQLITE_DB = 'dummy_data.db'

def sanitize_name(name: str) -> str:
    # Standardize sheet and column names for SQLite
    name = name.strip().lower()
    name = re.sub('[^a-z0-9_]+', '_', name)
    name = re.sub('_+', '_', name).strip('_')
    if not name:
        name = 'unnamed'
    if re.match('^\\d', name):
        name = f't_{name}'
    if name in {'table', 'select', 'from', 'where'}:
        name = f'{name}_col'
    return name

def dtype_to_sql(dtype) -> str:
    # Map pandas dtypes to SQLite types
    if pd.api.types.is_integer_dtype(dtype):
        return 'INTEGER'
    if pd.api.types.is_float_dtype(dtype):
        return 'REAL'
    if pd.api.types.is_bool_dtype(dtype):
        return 'INTEGER'
    if pd.api.types.is_datetime64_any_dtype(dtype):
        return 'TEXT'
    return 'TEXT'

def open_excel(file: str) -> Dict[str, pd.DataFrame]:
    # Load Excel file and clean sheet/column names
    if not os.path.exists(file):
        sys.exit(f'[ERROR] Excel file not found: {file}')
    xls = pd.ExcelFile(file)
    sheets = {}
    for sheet in xls.sheet_names:
        df = pd.read_excel(xls, sheet_name=sheet)
        new_cols = []
        for c in df.columns:
            new_cols.append(sanitize_name(str(c)))
        df.columns = new_cols
        for c in df.columns:
            if pd.api.types.is_datetime64_any_dtype(df[c]):
                df[c] = df[c].dt.strftime('%Y-%m-%d %H:%M:%S').astype('string')
        sheets[sanitize_name(sheet)] = df
    return sheets

def create_table_sql(table: str, df: pd.DataFrame) -> str:
    # Build CREATE TABLE statement from dataframe
    cols_sql = []
    for c in df.columns:
        coltype = dtype_to_sql(df[c].dtype)
        cols_sql.append(f'"{c}" {coltype}')
    has_id_like = any((c in df.columns for c in ['id', 'student_id', 'application_id']))
    pk = '' if has_id_like else ', "__rowid__" INTEGER PRIMARY KEY AUTOINCREMENT'
    return f'''CREATE TABLE "{table}" ({', '.join(cols_sql)}{pk});'''

def add_indexes(conn: sqlite3.Connection, table: str, df: pd.DataFrame) -> None:
    # Create helpful indexes on common columns
    idx_targets = ['id', 'student_id', 'application_id', 'offer_id', 'enrollment_id', 'visa_id', 'agent_id', 'term', 'intake', 'status', 'date', 'created_at', 'updated_at', 'offer_date', 'expiry_date', 'granted_date', 'lodged_date']
    existing = set(df.columns)
    made = 0
    for col in idx_targets:
        if col in existing:
            idx_name = f'idx_{table}_{col}'
            try:
                conn.execute(f'CREATE INDEX IF NOT EXISTS "{idx_name}" ON "{table}" ("{col}");')
                made += 1
            except Exception as e:
                print(f'[WARN] Could not create index on {table}.{col}: {e}')
    if made:
        print(f'  - Added {made} index(es) to {table}')

def write_table(conn: sqlite3.Connection, table: str, df: pd.DataFrame) -> None:
    # Drop and recreate table, then bulk insert rows
    cur = conn.cursor()
    cur.execute(f'DROP TABLE IF EXISTS "{table}";')
    cur.execute(create_table_sql(table, df))
    placeholders = ', '.join(['?'] * len(df.columns))
    collist = ', '.join([f'"{c}"' for c in df.columns])
    sql = f'INSERT INTO "{table}" ({collist}) VALUES ({placeholders})'
    rows = df.where(pd.notnull(df), None).values.tolist()
    cur.executemany(sql, rows)
    conn.commit()
    add_indexes(conn, table, df)
    print(f'[OK] Wrote {len(rows)} rows to {table}')

def main():
    # Convert Excel sheets into a fresh SQLite database
    sheets = open_excel(EXCEL_FILE)
    if not sheets:
        sys.exit('[ERROR] No sheets found.')
    if os.path.exists(SQLITE_DB):
        os.remove(SQLITE_DB)
    conn = sqlite3.connect(SQLITE_DB)
    try:
        for table, df in sheets.items():
            if df.empty:
                print(f'[SKIP] {table} is empty')
                continue
            write_table(conn, table, df)
    finally:
        conn.close()
    print(f'\nDone. Created SQLite DB: {SQLITE_DB}')
    print('You can now use it.')

if __name__ == '__main__':
    main()
