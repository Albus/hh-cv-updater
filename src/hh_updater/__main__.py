from datetime import datetime
from typing import List

import typer

# Импортируем наш класс HHUpdater
# Предполагается, что класс HHUpdater находится в файле hhupdater.py
from hh_updater import HHUpdater

verbose: bool = False
base_url: str = "https://hh.ru"
login: str | None = None
password: str | None = None

# Создаем экземпляр Typer приложения
app = typer.Typer (
	no_args_is_help = True ,
	name = "hh-updater" ,
	help = "CLI инструмент для автоматического обновления резюме на HH.ru" ,
	# epilog = ""
)


@app.callback ( )
def main (
		_verbose: bool = typer.Option ( verbose , "--verbose" , "-v" , help = "Подробный вывод" ) ,
		_base_url: str = typer.Option ( base_url , "--url" ,
		                                help = "Базовый URL HH.ru (можно изменить для тестирования)" ) ,
		_login: str = typer.Option ( ... , "--login" , prompt = True , hide_input = False ,
		                             help = "Логин (email) от аккаунта HH.ru" ) ,
		_password: str = typer.Option ( ... , "--password" , prompt = True , hide_input = True ,
		                                help = "Пароль от аккаунта HH.ru" ) ,
) :
	"""
	CLI инструмент для автоматического обновления резюме на HH.ru

	Позволяет автоматически "поднимать" резюме в поиске HH.ru
	для поддержания их актуальности.
	"""
	global verbose , base_url , login , password
	verbose = _verbose or False
	base_url = _base_url or None
	login = _login or None
	password = _password or None


def print_success ( message: str ) :
	"""Утилита для вывода успешных сообщений"""
	typer.echo ( typer.style ( f"✓ {message}" , fg = typer.colors.GREEN ) )


def print_error ( message: str ) :
	"""Утилита для вывода сообщений об ошибках"""
	typer.echo ( typer.style ( f"✗ {message}" , fg = typer.colors.RED ) )


def print_info ( message: str ) :
	"""Утилита для вывода информационных сообщений"""
	typer.echo ( typer.style ( f"ℹ {message}" , fg = typer.colors.BLUE ) )


@app.command ( )
def update (
		cv_ids: List [ str ] = typer.Argument ( ... , help = "Список ID резюме для обновления" ) ,
) :
	"""
	Обновить указанные резюме на HH.ru

	Примеры:
	hh-updater update cv123 cv456 --login user@email.com --password pass123
	"""

	if verbose :
		print_info ( f"Начинаем процесс обновления {len ( cv_ids )} резюме" )
		print_info ( f"Используем базовый URL: {base_url}" )
		print_info ( f"Резюме для обновления: {', '.join ( cv_ids )}" )

	start_time = datetime.now ( )

	try :
		# Используем контекстный менеджер для автоматического управления соединением
		with HHUpdater ( base_url ) as updater :
			if verbose :
				print_info ( "Получаем XSRF токен..." )

			# Авторизуемся на HH.ru
			if verbose :
				print_info ( "Выполняем авторизацию..." )

			auth_success = updater.auth ( login , password )

			if not auth_success :
				print_error ( "Ошибка авторизации. Проверьте логин и пароль." )
				raise typer.Exit ( code = 1 )

			print_success ( "Авторизация прошла успешно!" )

			# Обновляем каждое резюме
			success_count = 0
			for cv_id in cv_ids :
				if verbose :
					print_info ( f"Обновляем резюме {cv_id}..." )

				if updater.update_cv ( cv_id ) :
					print_success ( f"Резюме {cv_id} успешно обновлено!" )
					success_count += 1
				else :
					print_error ( f"Не удалось обновить резюме {cv_id}" )

			# Выводим итоговую статистику
			end_time = datetime.now ( )
			duration = (end_time - start_time).total_seconds ( )

			print_success ( f"Обновлено {success_count} из {len ( cv_ids )} резюме за {duration:.2f} секунд" )

			if success_count < len ( cv_ids ) :
				raise typer.Exit ( code = 1 )

	except Exception as e :
		print_error ( f"Произошла непредвиденная ошибка: {str ( e )}" )
		if verbose :
			import traceback
			typer.echo ( traceback.format_exc ( ) )
		raise typer.Exit ( code = 1 )


@app.command ( )
def check (
		base_url: str = typer.Option ( "https://hh.ru" , help = "Базовый URL для проверки доступности" )
) :
	"""
	Проверить доступность HH.ru и работу клиента
	"""
	print_info ( f"Проверяем доступность {base_url}..." )

	try :
		with HHUpdater ( base_url ) as updater :
			# Пытаемся получить XSRF токен - это проверит доступность сайта
			xsrf = updater.get_xsrf ( )

			if xsrf :
				print_success ( f"HH.ru доступен! XSRF токен получен: {xsrf [ :10 ]}..." )
			else :
				print_error ( "Не удалось получить XSRF токен" )
				raise typer.Exit ( code = 1 )

	except Exception as e :
		print_error ( f"Ошибка при проверке доступности: {str ( e )}" )
		raise typer.Exit ( code = 1 )


if __name__ == "__main__" :
	app ( )
