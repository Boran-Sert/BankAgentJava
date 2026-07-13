import asyncio
import logging
import uuid
from app.main import create_app
from app.api.endpoints import process_message, JavaRequest
from app.core.contracts import ServiceSpec

# Kütüphanelerin log kalabalığını azaltıp sadece kendi loglarımızı görmek için:
logging.getLogger("httpx").setLevel(logging.WARNING)


async def main():
    print("======================================================")
    print("🏦 HIERARCHICAL BANKING AI - TERMINAL DEMO (LANGGRAPH)")
    print("======================================================")
    print("Sistem mimarisi (VectorDB, LangGraph, Ollama) yükleniyor...\n")

    # Tüm mimariyi ayağa kaldıran fonksiyonumuzu çağırıyoruz (VDB seeding vs. için)
    app = create_app()

    print(
        "\n[SİSTEM HAZIR] Terminal üzerinden AI ile doğal dille konuşmaya başlayabilirsiniz."
    )
    print("Test Edebileceğiniz Örnek Niyetler (Intents):")
    print("- Kredi kartı borcumu ödemek istiyorum (MAKE_PAYMENT - MUTATING_CRITICAL)")
    print("- Hesap bakiyem ne kadar (GET_BALANCE - READ_ONLY)")
    print("Çıkmak için 'q' veya 'exit' yazın.\n")

    session_id = str(uuid.uuid4())
    user_id = "test_user_1"
    print(f"[BİLGİ] Yeni ve temiz bir oturum başlatıldı: {session_id}")

    while True:
        try:
            user_input = input("\n> Sen: ").strip()
            if not user_input:
                continue
            if user_input.lower() in ["q", "exit", "quit", "çık", "çıkış"]:
                print("Demo sonlandırılıyor...")
                break

            request = JavaRequest(
                session_id=session_id,
                user_id=user_id,
                message=user_input,
            )

            # API endpointinin doğrudan Python kodu olarak çağrılması
            response = await process_message(request)

            print("\n================ SİSTEM YANITI ================")
            print(f"Durum               : {response.status}\n")
            print(f"Aktif Intent        : {response.intent}\n")
            print(f"Toplanan Veriler    : {response.parameters}\n")
            if getattr(response, "thinking", None):
                print(f"AI iç sesi          : {response.thinking}\n")
            if response.message_to_user:
                print(f"Kullanıcıya Mesaj   : {response.message_to_user}")
            print("===============================================\n")

            if response.status == "COMPLETED":
                print(
                    "[ONAYLANDI] İşlem başarıyla sonuçlandı ve LangGraph döngüsü tamamlandı."
                )
                session_id = str(uuid.uuid4())
                print(f"-> Yeni bir oturum başlatılıyor: {session_id}\n")

            elif response.status == "FAILED":
                print("[HATA] İşlem iptal edildi veya sistem hatası oluştu.")
                session_id = str(uuid.uuid4())
                print(f"-> Yeni bir oturum başlatılıyor: {session_id}\n")

        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"Sistemsel Hata: {e}")


if __name__ == "__main__":
    asyncio.run(main())
