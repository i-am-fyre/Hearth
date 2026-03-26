import os

file_path = "/app/alembic/versions/7a1fd8a0f96f_initial_schema.py"

with open(file_path, "r") as f:
    content = f.read()

# 1. Remove the foreign key creation from the receipts table
content = content.replace(
    "    sa.ForeignKeyConstraint(['transaction_id'], ['transactions.id'], ),\n", 
    ""
)

# 2. Add the foreign key creation after the transactions table is created
replacement_2 = "op.create_index(op.f('ix_transactions_id'), 'transactions', ['id'], unique=False)\n    op.create_foreign_key('fk_receipts_transaction_id_transactions', 'receipts', 'transactions', ['transaction_id'], ['id'])"
content = content.replace(
    "op.create_index(op.f('ix_transactions_id'), 'transactions', ['id'], unique=False)", 
    replacement_2
)

# 3. Add the dropping of the foreign key before dropping the transactions table
replacement_3 = "op.drop_constraint('fk_receipts_transaction_id_transactions', 'receipts', type_='foreignkey')\n    op.drop_table('transactions')"
content = content.replace(
    "op.drop_table('transactions')", 
    replacement_3
)

with open(file_path, "w") as f:
    f.write(content)

print("Migration script successfully patched!")
