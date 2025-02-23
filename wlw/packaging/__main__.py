"""
Packaging helper.

Designed to be run as a standalone script, utilizing the `packaging` module.
"""

import argparse

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Package chapters into a single file.")
    parser.add_argument("chapters_dir", help="Directory containing chapters to package.")
    args = parser.parse_args()

    from wlw.packaging.package import package_chapters

    print(f"Packaging chapters in '{args.chapters_dir}'...")
    package_chapters("[n1h1raxem1l::4::eva]", args.chapters_dir)
    print("Done.")
