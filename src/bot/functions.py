import consts as MY_CONSTS

def getLoginPassword(chatId):
    # Проверяем, если такой chatId уже существует в нашей базе данных (если пользователь уже зарегистрирован)
    # то берем его логин (username) и формируем ему новый пароль (хеш-версию нового пароля клдаем в базу данных)
    # выдаем ему эти логин и пароль в строке ниже
    # после этого (или до этого) надо обязательно удалить accessToken и refreshToken из базы данных!!!

    # Если chatId не существует, то все тоже самое, только произвольно придумываем логин

    #Хотел обратить внимание, что логин и пароль не должен быть более нескольких символов,
    # так как пользователю надо будет его переписывать в комп
    result = dict(login='user01', password='sHk8b')
    return MY_CONSTS.YOUR_LOGIN + result.get("login") + '\n' + MY_CONSTS.YOUR_PASSWORD + result.get("password")


def getMagicLink(chatId):
    result = 'https://sbhsbj.com'
    return result
