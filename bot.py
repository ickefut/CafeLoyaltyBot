from telegram import Update, InputFile
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from qr_code import generate_qr_code as get_gr
from pyzbar.pyzbar import decode
from PIL import Image
import tempfile
import os

ADMIN_PASSWORD = "admin1234"
admin_id = None
awaiting_password = False  # Şifre bekleme durumu

# Müşteri puanları için bir sözlük
customer_scores = {}

# Admin şifresi kontrolü
async def admin_password_check(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    global admin_id, awaiting_password
    user_message = update.message.text

    if user_message == ADMIN_PASSWORD:
        admin_id = update.message.from_user.id
        awaiting_password = False  # Şifre bekleme durumu kapatılır
        await update.message.reply_text(f"Admin olarak tanımlandınız. Admin ID'niz: {admin_id}")
    else:
        awaiting_password = False  # Yanlış şifre durumunda da durumu sıfırla
        await update.message.reply_text("Geçersiz şifre. Lütfen /admin komutunu tekrar deneyin.")

# Admin olma komutu
async def admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    global awaiting_password
    if admin_id is not None:
        await update.message.reply_text("Admin zaten tanımlı.")
        return

    awaiting_password = True  # Şifre bekleme durumu açılır
    await update.message.reply_text("Admin şifresini girin:")

# QR Code alma fonksiyonu
async def get_qr(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    global admin_id
    if update.message.from_user.id != admin_id:
        await update.message.reply_text("Bu komutu yalnızca admin kullanabilir.")
        return

    # QR kod için veri oluştur (örneğin bir müşteri ID veya sipariş bilgisi)
    data = f"Admin ID: {admin_id}, Kullanıcı: {update.message.from_user.id}"
    
    # QR kodu oluştur ve dosya yolunu al
    qr_code_path = get_gr(data)
    
    # QR kodu görsel olarak gönder
    with open(qr_code_path, 'rb') as qr_file:
        await update.message.reply_photo(photo=InputFile(qr_file), caption=f"İşte oluşturduğunuz QR kod!")

# Müşteriden QR kodu alma ve puan ekleme fonksiyonu
async def receive_qr(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.message.from_user.id
    qr_code_image = update.message.photo[-1]  # Kullanıcının gönderdiği en büyük fotoğraf
    file = await qr_code_image.get_file()  # Fotoğrafı Telegram'dan alıyoruz

    # Geçici dosya oluşturuyoruz
    with tempfile.NamedTemporaryFile(delete=False) as temp_file:
        temp_file_name = temp_file.name
        await file.download_to_drive(temp_file_name)  # Fotoğrafı geçici dosyaya kaydediyoruz

    # QR kodunu çöz
    qr_data = decode_qr_code(temp_file_name)

    if qr_data:
        # QR kodu çözülürse
        await update.message.reply_text(f"QR kodu başarıyla çözüldü. Veri: {qr_data}")

        # Müşteri puanlarını güncelle
        if user_id not in customer_scores:
            customer_scores[user_id] = 0
        customer_scores[user_id] += 1

        if customer_scores[user_id] >= 5:
            # Bedava kahve QR kodu oluştur
            coffee_qr_code_path = get_gr("Bedava Kahve")
            with open(coffee_qr_code_path, 'rb') as qr_file:
                await update.message.reply_photo(photo=InputFile(qr_file), caption="Tebrikler! Bedava kahve kazandınız!")

            # Puanları sıfırlıyoruz, yeni ödüller kazanması için
            customer_scores[user_id] = 0
        else:
            await update.message.reply_text(f"QR kodunuz başarıyla alındı! Şu anki puanınız: {customer_scores[user_id]}")

    else:
        await update.message.reply_text("QR kodu çözülemedi. Lütfen geçerli bir QR kodu gönderin.")

    # Geçici dosyayı siliyoruz
    os.remove(temp_file_name)

# QR kodunu çözme fonksiyonu
def decode_qr_code(image_path):
    # Görüntüyü aç
    img = Image.open(image_path)
    # QR kodunu çöz
    decoded_objects = decode(img)
    for obj in decoded_objects:
        return obj.data.decode("utf-8")  # QR kodundaki veriyi döndür
    return None  # QR kodu bulunamadıysa None döndür

# Admin QR kodu yükleyip kullanıcıyı kontrol etme fonksiyonu
async def admin_verify_qr(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    global admin_id
    if update.message.from_user.id != admin_id:
        await update.message.reply_text("Bu komutu yalnızca admin kullanabilir.")
        return

    qr_code_image = update.message.photo[-1]  # Admin'in gönderdiği fotoğraf
    file = await qr_code_image.get_file()  # Fotoğrafı Telegram'dan alıyoruz

    # Geçici dosya oluşturuyoruz
    with tempfile.NamedTemporaryFile(delete=False) as temp_file:
        temp_file_name = temp_file.name
        await file.download_to_drive(temp_file_name)  # Fotoğrafı geçici dosyaya kaydediyoruz

    # QR kodunu çöz
    qr_data = decode_qr_code(temp_file_name)

    if qr_data:
        # QR kodundan kullanıcı ID'si alınıyor
        user_id = int(qr_data.split(":")[1].split(",")[0].strip())  # Admin tarafından oluşturulan QR kodu formatına göre
        if customer_scores.get(user_id, 0) >= 5:
            # Bedava kahve kazanan kullanıcı için mesaj
            await update.message.reply_text(f"{user_id} ID'li kullanıcı kahve kazandı.")
        else:
            await update.message.reply_text(f"{user_id} ID'li kullanıcı bedava kahve kazanmadı.")

    else:
        await update.message.reply_text("QR kodu çözülemedi. Lütfen geçerli bir QR kodu gönderin.")

    # Geçici dosyayı siliyoruz
    os.remove(temp_file_name)

# Start komutu
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("Hoş geldiniz! Eğer varsa QR kodunuzu paylaşabilirsiniz. Admin size bir QR kodu gösterdiğinde, onu buraya gönderebilirsiniz.")

# Botu çalıştırma
if __name__ == "__main__":
    app = ApplicationBuilder().token("7730666637:AAFpyriaQ2WRkdwaed3g55cd0s_uTUqdkJQ").build()  # BOT_TOKEN'ı botunuzun token'ı ile değiştirin

    # Handler'lar ekliyoruz
    app.add_handler(CommandHandler("get_qr", get_qr))
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("admin", admin_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, admin_password_check))
    app.add_handler(MessageHandler(filters.PHOTO, receive_qr))  # Fotoğraf mesajlarını alıyoruz
    app.add_handler(MessageHandler(filters.PHOTO, admin_verify_qr))  # Admin QR kodunu doğrulama

    app.run_polling()
