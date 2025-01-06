import os
import hashlib
import zipfile
import requests
# 配置信息
# target_directory = r"\\10.100.129.250\release\mcu\3F1324_AMP"  # 替换为你的目标文件夹路径
target_directory = r"D:\wulingtest"  # 替换为你的目标文件夹路径
jfrog_url = "https://Jfrog.sgmw.com.cn/artifactory/android-MCU/BC/latest/testJfrog/"  # 上传目标地址
username = "zhengyuliang_bicv"  # 用户名
password = "Zhengyuliang@bicv.com1"  # 密码


def find_latest_folder(directory):
    """查找指定目录下最新的文件夹"""
    # 获取所有子文件夹
    folders = [f for f in os.listdir(directory) if os.path.isdir(os.path.join(directory, f))]

    # 如果没有文件夹，返回 None
    if not folders:
        return None

    # 获取每个文件夹的修改时间
    folder_paths = [os.path.join(directory, folder) for folder in folders]
    latest_folder = max(folder_paths, key=os.path.getmtime)  # 获取最新修改的文件夹
    return latest_folder


def get_md5(file_path):
    """计算文件的MD5值"""
    hash_md5 = hashlib.md5()
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()


def create_md5_file(file_path):
    """创建一个 .MD5 文件，保存文件的md5值"""
    md5_value = get_md5(file_path)

    # 去掉原文件的 .bin 生成 .md5 文件
    md5_file_path = file_path.rsplit('.', 1)[0] + ".md5"
    with open(md5_file_path, 'w') as md5_file:
        md5_file.write(md5_value)
    print(f"MD5文件已保存为 {md5_file_path}")
    return md5_file_path


def rename_files_in_folder(directory):
    """遍历文件夹中的文件，并进行重命名"""
    folder_name = os.path.basename(directory.rstrip(os.sep))  # 获取文件夹名称
    files = sorted(os.listdir(directory))  # 排序文件列表

    renamed_files = []  # 用于保存重命名后的文件路径
    for file_name in files:
        file_path = os.path.join(directory, file_name)

        # 如果是文件而不是子文件夹
        if os.path.isfile(file_path):
            file_extension = os.path.splitext(file_name)[1]

            # 创建新的文件名，使用文件夹的名称 + 文件扩展名
            new_file_name = folder_name + file_extension
            new_file_path = os.path.join(directory, new_file_name)

            # 重命名文件
            os.rename(file_path, new_file_path)
            print(f"文件 {file_name} 重命名为 {new_file_name}")

            # 如果是 .bin 或 .srec 文件，保存其路径
            if file_extension.lower() in ['.bin', '.srec']:
                renamed_files.append(new_file_path)

            # 如果是 .bin ，计算并保存其 md5 值
            if file_extension.lower() in ['.bin',]:
                md5_file = create_md5_file(new_file_path)
                renamed_files.append(md5_file)

        # 如果是文件夹，递归调用
        elif os.path.isdir(file_path):
            renamed_files.extend(rename_files_in_folder(file_path))

    return renamed_files


def zip_files(files, output_zip):
    """将文件压缩成一个ZIP文件，避免重复添加文件"""
    added_files = set()  # 用于记录已添加的文件名
    with zipfile.ZipFile(output_zip, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for file in files:
            file_name = os.path.basename(file)
            if file_name not in added_files:
                zipf.write(file, file_name)  # 仅写入文件名而非绝对路径
                added_files.add(file_name)  # 标记为已添加
    print(f"已创建压缩文件：{output_zip}")


def upload_file_to_jfrog(file_path, url, user, pwd, version):
    """上传单个文件到 JFrog"""
    if not os.path.isfile(file_path):
        print(f"文件 {file_path} 不存在！")
        return

    # 构建上传的路径
    filename = os.path.basename(file_path)
    upload_url = f"{url}{version}/{filename}"

    # 读取文件并上传
    with open(file_path, 'rb') as file:
        print(f"正在上传 {file_path} 到 {upload_url}...")
        response = requests.put(upload_url, data=file, auth=(user, pwd))

    # 检查响应状态
    if response.status_code == 201:
        print(f"文件 {filename} 上传成功！")
    else:
        print(f"文件 {filename} 上传失败，状态码：{response.status_code}")
        print("响应信息：", response.text)


# 示例使用
if __name__ == "__main__":
    # 1. 查找最新的文件夹
    latest_folder = find_latest_folder(target_directory)

    if latest_folder:
        print(f"最新的文件夹是：{latest_folder}")

        # 获取最新的版本号（即文件夹名称）
        version = os.path.basename(latest_folder)

        # 2. 在最新的文件夹中进行重命名操作
        renamed_files = rename_files_in_folder(latest_folder)

        # 3. 压缩所有相关文件 (.bin, .srec, .md5 文件)
        if renamed_files:
            zip_file_name = os.path.join(latest_folder, f"{version}.zip")  # 使用版本号命名
            zip_files(renamed_files, zip_file_name)

            # 4. 上传压缩包到 JFrog
            upload_file_to_jfrog(zip_file_name, jfrog_url, username, password, version)
    else:
        print("没有找到需要上传的文件！")
else:
    print("没有找到任何文件夹！")
