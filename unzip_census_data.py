"""Unzip Compressed Folders of Census Data."""
import os
import zipfile


def main():
    """Unzip relevant boundaries and block geographies.

    We unzip county boundaries, state legislative districts, congressional
    districts, and census block geographies
    """
    # Create extracted directories if they do not exist
    create_extracted_directories()

    # Extract state legislative districts
    raw = 'raw_census/'
    ex = 'extract_census/'
    extract_entire_directory(raw + 'state_leg', ex + 'state_leg')

    # Extract congressional districts
    extract_entire_directory(raw + 'cd', ex + 'cd')

    # Extract counties
    extract_entire_directory(raw + 'county', ex + 'county')

    # Extract block geographies
    extract_entire_directory(raw + 'block_geo', ex + 'block_geo')
    return


def create_extracted_directories():
    """Create directories of files unzipped."""
    if not os.path.exists('extract_census'):
        os.makedirs('extract_census')

    if not os.path.exists('extract_census/block_geo'):
        os.makedirs('extract_census/block_geo')

    if not os.path.exists('extract_census/cd'):
        os.makedirs('extract_census/cd')

    if not os.path.exists('extract_census/county'):
        os.makedirs('extract_census/county')

    if not os.path.exists('extract_census/state_leg'):
        os.makedirs('extract_census/state_leg')
    return


def extract_entire_directory(compressed_directory, extracted_directory):
    """Extract zip folders from an entire directory.

    We only unzip if

    Arguments:
        compressed_directory: path to compressed zip folders

        extracted_directory: path to extracted directory
    """
    # Iterate through each zip folder
    folders = os.listdir(compressed_directory)
    for folder in folders:
        # Get compressed and extracted paths
        compressed_path = compressed_directory + '/' + folder
        extracted_path = extracted_directory + '/' + folder[:-4]

        # Extract if not already extracted
        if not os.path.exists(extracted_path):
            print(extracted_path)
            extract_zip_folder(compressed_path, extracted_path)
    return


def extract_zip_folder(compressed_path, extracted_path):
    """Unzip a zip folder.

    Arguments:
        compressed_path: path to compressed zip folder

        extracted_path: path after unzipping compressed folder
    """
    # Unzip the zip folder
    zip = zipfile.ZipFile(compressed_path, 'r')
    zip.extractall(extracted_path)
    zip.close()
    return


if __name__ == "__main__":
    main()
