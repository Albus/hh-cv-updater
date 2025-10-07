import httpx
from typing import Optional , Self

# Общие HTTP-заголовки для имитации браузера при запросах к HH.ru
# Эти заголовки помогают избежать блокировки и делают запросы более "человеческими"
COMMON_HEADERS: dict [ str , str ] = {
	'User-Agent'      : 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36' ,
	'Accept'          : 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8' ,
	'Accept-Encoding' : 'gzip, deflate, br' ,
	'Accept-Language' : 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7' ,
	'Connection'      : 'keep-alive' ,
	'DNT'             : '1'  # Do Not Track - указывает сайту, что мы не хотим отслеживания
}


# noinspection GrazieInspection,SpellCheckingInspection
class HHUpdater :
	"""
	Класс для автоматизации работы с HH.ru: авторизация и обновление резюме.

	Использует __slots__ для оптимизации памяти и производительности.
	Реализует контекстный менеджер для безопасного управления HTTP-соединениями.
	"""

	# __slots__ ограничивает возможные атрибуты экземпляра, экономя память
	# и предотвращая случайное создание новых атрибутов
	__slots__ = ('base_url' , 'client' , 'xsrf')

	def __init__ ( self , base_url: str = 'https://hh.ru' , / ) -> None :
		"""
		Инициализация клиента для работы с HH.ru.

		Args:
				base_url: Базовый URL HH.ru (по умолчанию 'https://hh.ru')
								 Символ / делает параметр позиционным - его нельзя передать по имени
		"""

		# Убираем завершающий слеш для единообразия URL
		self.base_url: str = base_url.rstrip ( '/' )
		# Создаем HTTP-клиент с общими заголовками и поддержкой редиректов
		self.client: httpx.Client = httpx.Client ( headers = COMMON_HEADERS , follow_redirects = True )
		# XSRF-токен для защиты от межсайтовой подделки запросов (будет получен позже)
		self.xsrf: Optional [ str ] = None

	def __enter__ ( self ) -> Self :
		"""
		Вход в контекстный менеджер.

		Returns:
				Self: Возвращает сам экземпляр класса для использования в блоке with
		"""

		return self

	def __exit__ (
			self , exc_type: Optional [ type ] , exc_val: Optional [ Exception ] , exc_tb: Optional [ object ] ) -> None :
		"""
		Выход из контекстного менеджера.

		Автоматически закрывает HTTP-клиент при выходе из блока with,
		даже если произошла ошибка.

		Args:
				exc_type: Тип исключения (если было)
				exc_val: Экземпляр исключения (если было)
				exc_tb: Traceback исключения (если было)
		"""

		self.client.close ( )

	def get_xsrf ( self ) -> Optional [ str ] :
		"""
		Получение XSRF-токена со страницы логина HH.ru.

		XSRF-токен необходим для защиты от межсайтовой подделки запросов
		и требуется при отправке форм авторизации.

		Returns:
				Optional[str]: XSRF-токен или None, если не удалось получить
		"""

		# Запрашиваем страницу логина, где в cookies будет XSRF-токен
		response: httpx.Response = self.client.get ( f"{self.base_url}/account/login?backurl=%2F" )

		# Извлекаем токен из cookies ответа
		self.xsrf = response.cookies.get ( '_xsrf' )

		return self.xsrf

	def auth ( self , login: str , password: str , / ) -> bool :
		"""
		Авторизация на HH.ru с использованием логина и пароля.

		Символ / делает параметры login и password позиционными -
		их нельзя передать по имени, только по позиции.

		Args:
				login: Логин (email) для входа в аккаунт HH.ru
				password: Пароль для входа в аккаунт HH.ru

		Returns:
				bool: True если авторизация успешна, иначе False
		"""

		# Если XSRF-токен еще не получен, запрашиваем его
		if not self.xsrf :
			self.get_xsrf ( )

		# Формируем данные для отправки формы авторизации
		data: dict [ str , str ] = {
			'username' : login ,  # Логин пользователя
			'password' : password ,  # Пароль пользователя
			'backUrl'  : f"{self.base_url}/" ,  # URL для редиректа после успешного входа
			'_xsrf'    : self.xsrf or '' ,  # XSRF-токен (защита от CSRF-атак)
			'action'   : 'Войти'  # Текст кнопки отправки формы
		}

		# Отправляем POST-запрос для авторизации
		response: httpx.Response = self.client.post (
			f"{self.base_url}/account/login?backurl=%2F" ,  # URL страницы логина
			data = data  # Данные формы авторизации
		)

		# Авторизация считается успешной, если сервер вернул статус 200 OK
		return response.status_code == 200

	def update_cv ( self , cv_id: str ) -> bool :
		"""
		Обновление времени последнего изменения резюме (поднятие в поиске).

		При обновлении резюме оно поднимается в результатах поиска работодателей.
		Это полезно для поддержания актуальности резюме в базе HH.ru.

		Args:
				cv_id: ID резюме, которое нужно обновить

		Returns:
				bool: True если обновление успешно, иначе False
		"""

		# Проверяем, что у нас есть XSRF-токен (значит, мы авторизованы)
		if not self.xsrf :
			return False

		# Формируем специальные заголовки для AJAX-запроса обновления резюме
		headers: dict [ str , str ] = {
			'X-Xsrftoken'      : self.xsrf ,  # XSRF-токен в заголовке (требуется HH.ru)
			'X-Requested-With' : 'XMLHttpRequest' ,  # Указываем, что это AJAX-запрос
			'Referer'          : f"{self.base_url}/applicant/resumes/{cv_id}"  # Страница-источник
		}

		# Данные для обновления резюме
		data: dict [ str , str ] = {
			'resume'       : cv_id ,  # ID обновляемого резюме
			'undirectable' : 'true'  # Флаг, предотвращающий редирект
		}

		# Отправляем POST-запрос для "касания" (обновления времени) резюме
		response: httpx.Response = self.client.post (
			f"{self.base_url}/applicant/resumes/touch" ,  # Эндпоинт для обновления
			data = data ,  # Данные с ID резюме
			headers = headers  # Специальные заголовки с токеном
		)

		# Обновление считается успешным, если сервер вернул статус 200 OK
		return response.status_code == 200