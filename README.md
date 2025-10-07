```python
from hh_updater import HHUpdater

# Использование с контекстным менеджером (рекомендуется)
with HHUpdater ( ) as updater :  # Используем URL по умолчанию (https://hh.ru)
	# Пытаемся авторизоваться
	if updater.auth ( "your_email@example.com" , "your_password" ) :
		print ( "Авторизация успешна!" )
		# Обновляем резюме с указанным ID
		if updater.update_cv ( "1234567890abcdef" ) :
			print ( "Резюме успешно обновлено!" )
		else :
			print ( "Ошибка при обновлении резюме" )
	else :
		print ( "Ошибка авторизации" )

# Или с кастомным URL (например, для тестирования)
with HHUpdater ( "https://test.hh.ru" ) as test_updater :
	test_updater.auth ( "test_user" , "test_password" )
	test_updater.update_cv ( "test_cv_id" )
```