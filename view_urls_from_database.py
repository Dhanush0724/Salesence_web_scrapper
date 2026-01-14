"""
Simple script to view stored product URLs
Usage: python view_urls.py
"""

import sqlite3
from datetime import datetime


def view_all_urls(db_path='product_urls.db', limit=50):
    """View all URLs in database"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get total count
    cursor.execute('SELECT COUNT(*) FROM product_urls')
    total = cursor.fetchone()[0]
    
    print(f"\n{'='*80}")
    print(f"STORED PRODUCT URLs (showing {min(limit, total)} of {total:,} total)")
    print(f"{'='*80}\n")
    
    # Get URLs
    cursor.execute(f'''
        SELECT id, url, category, status, created_at 
        FROM product_urls 
        ORDER BY id DESC 
        LIMIT {limit}
    ''')
    
    for row in cursor.fetchall():
        id_, url, category, status, created = row
        print(f"{id_:4d} | {category:15s} | {status:10s} | {url}")
    
    conn.close()


def view_by_category(db_path='product_urls.db'):
    """View URLs grouped by category"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT category, COUNT(*) as count
        FROM product_urls
        GROUP BY category
        ORDER BY count DESC
    ''')
    
    print(f"\n{'='*80}")
    print("URLs BY CATEGORY")
    print(f"{'='*80}\n")
    
    for category, count in cursor.fetchall():
        print(f"{category:20s}: {count:,} URLs")
    
    conn.close()


def view_by_status(db_path='product_urls.db'):
    """View URLs grouped by status"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT status, COUNT(*) as count
        FROM product_urls
        GROUP BY status
    ''')
    
    print(f"\n{'='*80}")
    print("URLs BY STATUS")
    print(f"{'='*80}\n")
    
    for status, count in cursor.fetchall():
        print(f"{status:15s}: {count:,} URLs")
    
    conn.close()


def export_to_txt(db_path='product_urls.db', output_file='all_urls.txt'):
    """Export all URLs to text file"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute('SELECT url FROM product_urls ORDER BY category, id')
    
    with open(output_file, 'w', encoding='utf-8') as f:
        for row in cursor.fetchall():
            f.write(row[0] + '\n')
    
    conn.close()
    
    print(f"\n✓ All URLs exported to: {output_file}")


def export_by_category(db_path='product_urls.db'):
    """Export URLs to separate files by category"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get all categories
    cursor.execute('SELECT DISTINCT category FROM product_urls WHERE category IS NOT NULL')
    categories = [row[0] for row in cursor.fetchall()]
    
    print(f"\n{'='*80}")
    print("EXPORTING BY CATEGORY")
    print(f"{'='*80}\n")
    
    for category in categories:
        cursor.execute('SELECT url FROM product_urls WHERE category = ?', (category,))
        urls = [row[0] for row in cursor.fetchall()]
        
        filename = f'urls_{category}.txt'
        with open(filename, 'w', encoding='utf-8') as f:
            for url in urls:
                f.write(url + '\n')
        
        print(f"✓ {category:15s}: {len(urls):4d} URLs → {filename}")
    
    conn.close()


def export_to_csv(db_path='product_urls.db', output_file='urls.csv'):
    """Export to CSV for Excel"""
    import csv
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT id, url, category, status, created_at
        FROM product_urls
        ORDER BY id
    ''')
    
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['ID', 'URL', 'Category', 'Status', 'Created At'])
        writer.writerows(cursor.fetchall())
    
    conn.close()
    
    print(f"\n✓ CSV exported to: {output_file}")


def search_urls(db_path='product_urls.db', search_term=''):
    """Search URLs containing a term"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT id, url, category, status
        FROM product_urls
        WHERE url LIKE ?
        LIMIT 100
    ''', (f'%{search_term}%',))
    
    results = cursor.fetchall()
    
    print(f"\n{'='*80}")
    print(f"SEARCH RESULTS for '{search_term}' ({len(results)} found)")
    print(f"{'='*80}\n")
    
    for row in results:
        id_, url, category, status = row
        print(f"{id_:4d} | {category:15s} | {url}")
    
    conn.close()


def delete_first_n_urls(db_path='product_urls.db', n=10):
    """Delete the first N URLs with 'pending' status from the database"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get the first N URLs with pending status to show what will be deleted
    cursor.execute(f'''
        SELECT id, url, category, status
        FROM product_urls
        WHERE status = 'pending'
        ORDER BY id ASC
        LIMIT {n}
    ''')
    
    urls_to_delete = cursor.fetchall()
    
    if not urls_to_delete:
        print("\nNo pending URLs to delete!")
        conn.close()
        return
    
    print(f"\n{'='*80}")
    print(f"PENDING URLS TO BE DELETED (First {len(urls_to_delete)})")
    print(f"{'='*80}\n")
    
    for id_, url, category, status in urls_to_delete:
        print(f"{id_:4d} | {category:15s} | {status:10s} | {url}")
    
    # Confirm deletion
    confirm = input(f"\nDelete these {len(urls_to_delete)} pending URLs? (yes/no): ").strip().lower()
    
    if confirm == 'yes':
        # Get the IDs to delete
        ids_to_delete = [row[0] for row in urls_to_delete]
        placeholders = ','.join('?' * len(ids_to_delete))
        
        cursor.execute(f'DELETE FROM product_urls WHERE id IN ({placeholders})', ids_to_delete)
        conn.commit()
        
        print(f"\n✓ Successfully deleted {len(urls_to_delete)} pending URLs!")
    else:
        print("\n✗ Deletion cancelled.")
    
    conn.close()


def interactive_menu():
    """Interactive menu to view URLs"""
    db_path = 'product_urls.db'
    
    while True:
        print(f"\n{'='*80}")
        print("PRODUCT URL VIEWER")
        print(f"{'='*80}")
        print("\n1. View all URLs (first 50)")
        print("2. View URLs by category")
        print("3. View URLs by status")
        print("4. Export all URLs to text file")
        print("5. Export URLs by category (separate files)")
        print("6. Export to CSV (Excel)")
        print("7. Search URLs")
        print("8. View custom number of URLs")
        print("9. Delete first N URLs")
        print("0. Exit")
        
        choice = input("\nEnter choice: ").strip()
        
        if choice == '1':
            view_all_urls(db_path, limit=50)
        
        elif choice == '2':
            view_by_category(db_path)
        
        elif choice == '3':
            view_by_status(db_path)
        
        elif choice == '4':
            export_to_txt(db_path)
        
        elif choice == '5':
            export_by_category(db_path)
        
        elif choice == '6':
            export_to_csv(db_path)
        
        elif choice == '7':
            term = input("Enter search term: ").strip()
            search_urls(db_path, term)
        
        elif choice == '8':
            try:
                limit = int(input("How many URLs to display? "))
                view_all_urls(db_path, limit=limit)
            except ValueError:
                print("Invalid number!")
        
        elif choice == '9':
            try:
                n = int(input("How many pending URLs to delete from the top? "))
                delete_first_n_urls(db_path, n=n)
            except ValueError:
                print("Invalid number!")
        
        elif choice == '0':
            print("\nGoodbye!")
            break
        
        else:
            print("\nInvalid choice!")


if __name__ == "__main__":
    interactive_menu()