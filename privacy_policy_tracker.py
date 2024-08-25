import requests
from bs4 import BeautifulSoup
import difflib
from waybackpy import WaybackMachineCDXServerAPI

def fetch_archived_versions(url):
    wayback = WaybackMachineCDXServerAPI(url, "json")
    snapshots = list(wayback.snapshots())
    
    # Get the first, last, and three middle snapshots
    if len(snapshots) > 5:
        first_snapshot = snapshots[0]
        last_snapshot = snapshots[-1]
        middle_snapshots = [
            snapshots[len(snapshots) // 4],
            snapshots[len(snapshots) // 2],
            snapshots[3 * len(snapshots) // 4]
        ]
        selected_snapshots = [first_snapshot] + middle_snapshots + [last_snapshot]
    else:
        selected_snapshots = snapshots  # If less than or equal to 5 snapshots, use them all

    return [(snapshot.archive_url, snapshot.timestamp) for snapshot in selected_snapshots]

def fetch_version_content(archive_url):
    response = requests.get(archive_url)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, 'html.parser')
    return soup.get_text()

def diff_texts(text1, text2, fromfile, tofile):
    diff = difflib.unified_diff(text1.splitlines(), text2.splitlines(), fromfile=fromfile, tofile=tofile, lineterm="")
    return "\n".join(diff)

def main(url, output_filename):
    print("Fetching archived versions...")
    archived_versions = fetch_archived_versions(url)
    
    if len(archived_versions) < 2:
        print("Not enough versions to compare.")
        return
    
    # Compare each version with the next one and save the diff
    with open(output_filename, 'w', encoding="utf-8") as diff_file:
        for i in range(len(archived_versions) - 1):
            archive_url1, timestamp1 = archived_versions[i]
            archive_url2, timestamp2 = archived_versions[i + 1]
            
            print(f"Fetching version from {timestamp1}...")
            version1 = fetch_version_content(archive_url1)
            
            print(f"Fetching version from {timestamp2}...")
            version2 = fetch_version_content(archive_url2)
            
            diff = diff_texts(version1, version2, f"Version_{timestamp1}.txt", f"Version_{timestamp2}.txt")
            
            if diff:
                diff_file.write(f"Changes from {timestamp1} to {timestamp2}:\n")
                diff_file.write(diff)
                diff_file.write("\n" + "-"*80 + "\n")
    
    print(f"Differences saved to {output_filename}")

if __name__ == "__main__":
    privacy_policy_url = "https://openai.com/policies/privacy-policy/"
    output_file = "privacy_policy_diffs.diff"
    main(privacy_policy_url, output_file)