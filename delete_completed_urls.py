"""
Quick Script to Delete Completed URLs from Database
This permanently removes all URLs with status = 'completed'
"""

import sqlite3

DATABASE_FILE = 'product_urls.db'


def delete_completed_urls():
    """Delete all completed URLs from the database"""

    print("\n" + "=" * 80)
    print("DELETE COMPLETED URLS")
    print("=" * 80 + "\n")

    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()

    # Count completed URLs
    cursor.execute("SELECT COUNT(*) FROM product_urls WHERE status = 'completed'")
    completed_count = cursor.fetchone()[0]

    if completed_count == 0:
        print("✓ No completed URLs found. Nothing to delete.")
        conn.close()
        return

    print(f"Found {completed_count} completed URLs\n")

    # Show breakdown by category
    cursor.execute("""
        SELECT category, COUNT(*) 
        FROM product_urls
        WHERE status = 'completed'
        GROUP BY category
    """)

    print("Completed URLs by Category:")
    print("-" * 40)
    for category, count in cursor.fetchall():
        print(f"  {category}: {count}")

    print("\n" + "=" * 80)
    choice = input(
        f"\nPermanently DELETE all {completed_count} completed URLs? (yes/no): "
    ).strip().lower()

    if choice == "yes":
        cursor.execute("DELETE FROM product_urls WHERE status = 'completed'")
        conn.commit()

        print(f"\n✓ Successfully deleted {completed_count} completed URLs")

        # Show updated stats
        cursor.execute("""
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN status = 'pending' THEN 1 ELSE 0 END) as pending,
                SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed,
                SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed
            FROM product_urls
        """)

        total, pending, completed, failed = cursor.fetchone()

        print(f"\nUpdated Database Stats:")
        print(f"  Total:     {total}")
        print(f"  Pending:   {pending}")
        print(f"  Completed: {completed}")
        print(f"  Failed:    {failed}")

    else:
        print("\n✗ Deletion cancelled. No changes made.")

    conn.close()
    print("\n" + "=" * 80 + "\n")


if __name__ == "__main__":
    delete_completed_urls()
