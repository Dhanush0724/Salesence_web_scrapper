"""
Quick Script to Reset Failed URLs to Pending Status
This allows you to retry them with the improved scraper
"""

import sqlite3

DATABASE_FILE = 'product_urls.db'

def reset_failed_to_pending():
    """Reset all failed URLs to pending status"""
    
    print("\n" + "="*80)
    print("RESET FAILED URLS TO PENDING")
    print("="*80 + "\n")
    
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    
    # Count failed URLs
    cursor.execute("SELECT COUNT(*) FROM product_urls WHERE status = 'failed'")
    failed_count = cursor.fetchone()[0]
    
    if failed_count == 0:
        print("✓ No failed URLs found. Nothing to reset.")
        conn.close()
        return
    
    print(f"Found {failed_count} failed URLs\n")
    
    # Show breakdown by category
    cursor.execute("""
        SELECT category, COUNT(*) 
        FROM product_urls 
        WHERE status = 'failed'
        GROUP BY category
    """)
    
    print("Failed URLs by Category:")
    print("-" * 40)
    for category, count in cursor.fetchall():
        print(f"  {category}: {count}")
    
    print("\n" + "="*80)
    choice = input(f"\nReset all {failed_count} failed URLs to 'pending'? (yes/no): ").strip().lower()
    
    if choice == 'yes':
        cursor.execute("UPDATE product_urls SET status = 'pending' WHERE status = 'failed'")
        conn.commit()
        
        print(f"\n✓ Successfully reset {failed_count} URLs to 'pending' status")
        print("\nYou can now run the scraper again:")
        print("  py scrapper.py")
        
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
        print("\n✗ Reset cancelled. No changes made.")
    
    conn.close()
    print("\n" + "="*80 + "\n")


if __name__ == "__main__":
    reset_failed_to_pending()