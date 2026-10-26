# Unix/Linux Dosya Erişim İzinleri Simülatörü

## Proje Hakkında

Bu proje, Unix/Linux tabanlı işletim sistemlerindeki dosya erişim yetkilendirme mekanizmasını (POSIX izin modeli) görselleştirmek ve uygulamalı olarak test etmek amacıyla geliştirilmiş masaüstü simülasyon aracıdır.

Uygulama; kullanıcılar, kullanıcı grupları, sahiplik ilişkileri, `rwx` (Read, Write, Execute) izin bitleri ile sekizlik (octal) `chmod` ve `chown` komutlarının işleyişini gerçek zamanlı bir grafiksel kullanıcı arayüzü (GUI) üzerinden modeller.

---

## Temel Özellikler

* **Unix Yetkilendirme ve Erişim Denetimi:**
  * Kullanıcı (User), Grup (Group) ve Diğerleri (Others) için 3 basamaklı sekizlik izin ayrıştırması (örn. 755, 644, 600).
  * Okuma (r: 4), Yazma (w: 2) ve Çalıştırma (x: 1) haklarının bitsel mantık operasyonlarıyla (`&`, `|`) anlık doğrulanması.
  * `root` süper kullanıcısı için izin baypas kuralları.
* **chmod ve chown Yönetimi:**
  * Sadece dosya sahibi veya `root` tarafından yürütülebilen güvenli `chmod` mekanizması.
  * Yalnızca `root` yetkisiyle sınırlı `chown` sahiplik aktarımı.
* **Kullanıcı ve Grup Yönetimi:**
  * Yeni kullanıcı ve grup tanımlama, çoklu grup üyeliği desteği.
  * Kullanıcı silme durumunda yetim kalan dosyaların sahipliğinin otomatik olarak `root` kullanıcısına devredilmesi.
* **Dosya İşlemleri ve Simülasyon:**
  * Okuma (`r`), metin ekleyerek düzenleme (`w`) ve dosya uzantısına göre mantıksal çalıştırma (`x`) testleri.
  * Yetkisiz erişim girişimlerinde görsel uyarı ve sistem günlüğü (audit log) kaydı.
* **Veri Kalıcılığı:**
  * Tüm kullanıcı ve dosya meta verilerinin (oluşturulma, değiştirilme, son erişim damgaları) JSON formatında disk üzerinde kalıcı olarak saklanması.

---

## Kullanılan Teknolojiler

* **Programlama Dili:** Python 3.8+
* **Arayüz Kütüphanesi:** CustomTkinter (Modern Tkinter Sarmalayıcısı)
* **Veri Depolama:** JSON (Yerel Dosya Sistemi Simülasyonu)
* **Masaüstü Teması:** Sistem uyumlu Açık/Koyu Tema Desteği

---

## Proje Dizin Yapısı

```text
├── dosya_erisim_simulatoru.py      # Uygulama ana kaynak kodu ve GUI bileşenleri
├── filesystem_data_modern.json     # Kullanıcı ve dosya izin veritabanı (otomatik üretilir)
└── README.md                       # Proje dokümantasyonu
