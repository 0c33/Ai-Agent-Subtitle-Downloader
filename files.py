from scp import SCPClient
import paramiko, os
from zipfile import ZipFile
from io import BytesIO

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
# ip, user, pass v v v
ssh.connect('', username='', password='')

scp = SCPClient(ssh.get_transport())

def Save_File(Episode_Path, Subtitle_Path):

    file_path = Episode_Path.split('/')[-1]

    final_file_name = file_path.split('.')[0] # Episode File Name

    new_path = os.path.join('Downloads', f'{final_file_name}.ara.{Subtitle_Path.split('.')[-1].lower()}')

    

    counter = 0

    while os.path.exists(new_path):

        counter += 1
        final_name = f'{final_file_name}.ara.{counter}.{Subtitle_Path.split('.')[-1].lower()}'

        new_path = os.path.join('Downloads', final_name)

        if counter >= 4: break

    try:

        os.rename(f'Downloads\\{Subtitle_Path}', new_path)

    except Exception as e:
        print(f'Error renaming file: {e}')

    Move_File_To_Server(new_path, Episode_Path.split(Episode_Path.split('/')[-1])[0])


def Move_File_To_Server(local_path, remote_path):

    scp.put(local_path, remote_path)

    os.remove(local_path)


def Extract_Files(downloaded_content):

    with ZipFile(BytesIO(downloaded_content)) as content:

        os.makedirs('Downloads', exist_ok = True)

        ls = []

        for file_info in content.infolist():

            print(f'Content: {file_info.filename}')

            subtitle_ext = file_info.filename.split('.')[-1].lower()

            if subtitle_ext in ['srt', 'ass', 'vtt', 'sub', 'ssa']:

                print(f'This is file info: {file_info}\n\n\n')

                extracted_path = content.extract(file_info, 'Downloads')

                print(f'This is extracted_path: {extracted_path}\n\n\n')

                ls.append(file_info.filename)

        return ls
    

def Extract_File(file_content, content):

    subtitle_ext = file_content.filename.split('.')[-1].lower()

    if subtitle_ext in ['srt', 'ass', 'vtt', 'sub', 'ssa']:

        extracted_path = content.extract(file_content, 'Downloads')

        return extracted_path
    

def Get_Content(downloaded_content):

    with ZipFile(BytesIO(downloaded_content)) as content:
        
        ls = []

        for file_info in content.infolist():

            ls.append({
                "File_Name": file_info.filename,
                "File_Content": file_info
            })

    return (ls, content)