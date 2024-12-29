import qrcode
import os

# QR kod üretim fonksiyonu
def generate_qr_code(data: str, output_dir="qr_codes"):
    """
    Verilen veriye göre QR kod oluşturur ve kaydeder.

    Args:
        data (str): QR kodun içereceği veri.
        output_dir (str): QR kodların kaydedileceği klasör.
    """
    # Klasör yoksa oluştur
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Sıradaki dosya numarasını belirle
    existing_files = os.listdir(output_dir)
    next_number = len(existing_files) + 1
    file_name = f"qr_{next_number}.png"
    file_path = os.path.join(output_dir, file_name)

    # QR kod oluştur ve kaydet
    qr = qrcode.make(data)
    qr.save(file_path)

    return file_path
