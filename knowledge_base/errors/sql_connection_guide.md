# راهنمای رفع خطاهای اتصال به SQL Server در نرم‌افزار سپهریار

## خطای ۱: Login failed for user
* **علت:** نام کاربری یا کلمه عبور وارد شده در ارتباط SQL Server نادرست است.
* **راه حل:** 
  ۱. در صورت استفاده از احراز هویت ویندوز، اطمینان حاصل کنید کاربر ویندوز دسترسی `sysadmin` یا `db_datareader` دارد.
  ۲. وضعیت SQL Server and Windows Authentication mode را در Properties سرور بررسی کنید.

## خطای ۲: Named Pipes / TCP Provider: The system cannot find the file specified
* **علت:** سرویس SQL Server متوقف است یا نام Instance اشتباه وارد شده است.
* **راه حل:**
  ۱. سرویس `MSSQL$SEPEHRYAR2019` را در `services.msc` بررسی و Start کنید.
  ۲. در SQL Server Configuration Manager، وضعیت پروتکل TCP/IP و Named Pipes را در حالت Enabled قرار دهید.

## خطای ۳: Recovery Pending روی دیتابیس
* **علت:** فایل LDF یا MDF دیتابیس قفل شده یا فضای دیسک به پایان رسیده است.
* **راه حل:**
  ۱. ابتدا فضای آزاد درایو دیتابیس را بررسی کنید.
  ۲. سرویس SQL را ری‌استارت کرده و با دستور `ALTER DATABASE ... SET ONLINE` بررسی کنید.
