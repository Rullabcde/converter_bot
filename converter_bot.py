import os
import telebot
from pdf2docx import Converter
from docx2pdf import convert
from PIL import Image
import img2pdf

BOT_TOKEN = 'TOKEN'

bot = telebot.TeleBot(BOT_TOKEN)

# Direktori untuk menyimpan file sementara
DOWNLOAD_DIR = 'downloads/'
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# Simpan file yang diunggah sementara
user_files = {}

@bot.message_handler(commands=['start'])
def send_welcome(message):
    welcome_text = """
    Selamat datang di File Converter Bot! 
    Kirim file yang ingin Anda konversi, dan saya akan membantumu.
    """
    bot.reply_to(message, welcome_text)

@bot.message_handler(content_types=['document'])
def handle_document(message):
    try:
        # Download file
        file_info = bot.get_file(message.document.file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        
        # Simpan file
        file_name = message.document.file_name
        file_path = os.path.join(DOWNLOAD_DIR, file_name)
        
        with open(file_path, 'wb') as new_file:
            new_file.write(downloaded_file)
        
        # Simpan informasi file untuk pengguna
        user_files[message.chat.id] = {
            'original_path': file_path,
            'file_name': file_name,
            'file_ext': os.path.splitext(file_name)[1].lower()
        }
        
        # Tentukan opsi konversi berdasarkan ekstensi file
        markup = telebot.types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
        
        # Sesuaikan pilihan konversi berdasarkan tipe file
        if file_name.lower().endswith('.docx'):
            markup.add(
                telebot.types.KeyboardButton('Konversi ke PDF'),
                telebot.types.KeyboardButton('Batalkan')
            )
        elif file_name.lower().endswith('.pdf'):
            markup.add(
                telebot.types.KeyboardButton('Konversi ke Word'),
                telebot.types.KeyboardButton('Batalkan')
            )
        elif file_name.lower().endswith(('.jpg', '.jpeg', '.png')):
            markup.add(
                telebot.types.KeyboardButton('Konversi ke PDF'),
                telebot.types.KeyboardButton('Batalkan')
            )
        else:
            markup.add(telebot.types.KeyboardButton('Batalkan'))
        
        # Kirim pesan dengan pilihan konversi
        bot.reply_to(message, "Pilih opsi konversi:", reply_markup=markup)
    
    except Exception as e:
        bot.reply_to(message, f"Terjadi kesalahan: {str(e)}")

@bot.message_handler(func=lambda message: True)
def handle_conversion(message):
    chat_id = message.chat.id
    
    # Cek apakah pengguna memiliki file yang diunggah
    if chat_id not in user_files:
        return
    
    file_info = user_files[chat_id]
    file_path = file_info['original_path']
    file_name = file_info['file_name']
    file_ext = file_info['file_ext']
    
    try:
        # Batalkan proses
        if message.text == 'Batalkan':
            os.remove(file_path)
            del user_files[chat_id]
            bot.reply_to(message, "Proses dibatalkan.", reply_markup=telebot.types.ReplyKeyboardRemove())
            return
        
        # Konversi file
        output_file = None
        
        if message.text == 'Konversi ke PDF':
            if file_ext == '.docx':
                output_path = os.path.join(DOWNLOAD_DIR, f"{os.path.splitext(file_name)[0]}.pdf")
                convert(file_path, output_path)
                output_file = output_path
            
            elif file_ext in ['.jpg', '.jpeg', '.png']:
                output_path = os.path.join(DOWNLOAD_DIR, f"{os.path.splitext(file_name)[0]}.pdf")
                with open(output_path, "wb") as f:
                    f.write(img2pdf.convert(file_path))
                output_file = output_path
        
        elif message.text == 'Konversi ke Word':
            if file_ext == '.pdf':
                output_path = os.path.join(DOWNLOAD_DIR, f"{os.path.splitext(file_name)[0]}.docx")
                cv = Converter(file_path)
                cv.convert(output_path)
                cv.close()
                output_file = output_path
        
        # Kirim file hasil konversi
        if output_file:
            with open(output_file, 'rb') as convert_file:
                bot.send_document(chat_id, convert_file)
            
            # Hapus file sementara
            os.remove(file_path)
            os.remove(output_file)
            del user_files[chat_id]
            
            # Hapus keyboard
            bot.send_message(chat_id, "Konversi selesai.", reply_markup=telebot.types.ReplyKeyboardRemove())
        else:
            bot.reply_to(message, "Maaf, konversi tidak didukung.")
            os.remove(file_path)
            del user_files[chat_id]
    
    except Exception as e:
        bot.reply_to(message, f"Terjadi kesalahan: {str(e)}")
        os.remove(file_path)
        del user_files[chat_id]

# Jalankan bot
bot.polling()