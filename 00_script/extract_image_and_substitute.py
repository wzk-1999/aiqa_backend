import os
import zipfile
import pypandoc
import re


def convert_docx_to_format(input_docx_path, output_format, base_markdown_dir, base_doc_dir):
    docx_path = os.path.abspath(input_docx_path)
    if not os.path.exists(docx_path):
        raise FileNotFoundError(f"The file {docx_path} does not exist.")

    # Calculate the parallel output directory for the Markdown file
    relative_path = os.path.relpath(docx_path, base_doc_dir)
    output_dir = os.path.join(base_markdown_dir, os.path.dirname(relative_path))
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Generate the Markdown file path
    base_name = os.path.splitext(os.path.basename(docx_path))[0]
    output_path = os.path.join(output_dir, f"{base_name}.{output_format}")
    print(f"Converting {docx_path} to {output_path}")
    pypandoc.convert_file(docx_path, output_format, outputfile=output_path, extra_args=['--from=docx', '--to=markdown-grid_tables'])
    return output_path


def extract_images_from_docx(input_docx_path, base_image_dir, base_doc_dir):
    # Get the relative path to keep parallel structure in the image directory
    relative_path = os.path.relpath(input_docx_path, base_doc_dir)
    docx_dir_name = os.path.dirname(relative_path)
    docx_base_name = os.path.splitext(os.path.basename(input_docx_path))[0]

    # Set up the media directory path with spaces removed
    media_dir = os.path.join(base_image_dir, remove_spaces_from_path(docx_dir_name), remove_spaces_from_path(docx_base_name))
    if not os.path.exists(media_dir):
        os.makedirs(media_dir)

    # Extract images
    with zipfile.ZipFile(input_docx_path, 'r') as docx_zip:
        for file_info in docx_zip.infolist():
            if file_info.filename.startswith('word/media/'):
                image_name = os.path.basename(file_info.filename)
                extracted_image_path = os.path.join(media_dir, image_name)
                with open(extracted_image_path, 'wb') as image_file:
                    print(f"Extracting image {file_info.filename} to {extracted_image_path}")
                    image_file.write(docx_zip.read(file_info))

    return media_dir


def adjust_image_paths(markdown_path, media_dir, base_image_dir):
    # Calculate the relative path for Nginx (URL path only, starting from /image)
    relative_media_dir = os.path.relpath(media_dir, base_image_dir).replace('\\', '/')
    base_url = f"/image/{relative_media_dir}"

    with open(markdown_path, 'r', encoding='utf-8') as file:
        content = file.read()

    # Remove spaces from the image paths in the Markdown content
    content = re.sub(r'\(media/([^)]+)\)', lambda match: f"(media/{remove_spaces_from_path(match.group(1))})", content)

    # Update image paths in the Markdown file
    updated_content = re.sub(
        r'!\[([^\]]*)\]\(media/([^)]+)\)\s*\{[^}]*\}',  # Matches image annotations with optional `{}` parts
        lambda match: f"![{match.group(1)}]({base_url}/{remove_spaces_from_path(match.group(2))})",
        content
    )

    # Save the modified content
    with open(markdown_path, 'w', encoding='utf-8') as file:
        file.write(updated_content)
        print(f"Adjusted image paths in {markdown_path} to use /image/... URLs and removed size annotations.")


def remove_spaces_from_path(path):
    return re.sub(r'\s+', '', path)


def process_all_docx(base_doc_dir, base_markdown_dir, base_image_dir):
    for root, dirs, files in os.walk(base_doc_dir):
        for file in files:
            if file.endswith('.docx'):
                docx_path = os.path.join(root, file)
                markdown_path = convert_docx_to_format(docx_path, "md", base_markdown_dir, base_doc_dir)
                media_dir = extract_images_from_docx(docx_path, base_image_dir, base_doc_dir)
                adjust_image_paths(markdown_path, media_dir, base_image_dir)


def main():
    base_doc_dir = r'C:\Users\10648\Downloads\常见问题文档'
    base_markdown_dir = r'C:\Users\10648\Downloads\markdown'
    base_image_dir = r'C:\Users\10648\Downloads\image'
    print(f"Processing all docx files in {base_doc_dir}")
    process_all_docx(base_doc_dir, base_markdown_dir, base_image_dir)


if __name__ == "__main__":
    main()