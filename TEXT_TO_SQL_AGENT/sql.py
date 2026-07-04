from sqlite_connection import execute_sql

print(execute_sql("DROP TABLE transactions"))
print(execute_sql("DELETE FROM transactions WHERE 1=1"))
print(execute_sql("SELECT 1; DROP TABLE transactions;"))
print(execute_sql("SELECT COUNT(*) as total FROM transactions"))  # should still work normally