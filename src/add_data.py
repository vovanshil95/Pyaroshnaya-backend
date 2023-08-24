import asyncio
import uuid
import json

from database import async_session_maker

from questions.models import Category, Question, Prompt, Option

first_id = uuid.uuid4()
second_id = uuid.uuid4()
third_id = uuid.uuid4()
fourth_id = uuid.uuid4()
fifth_id = uuid.uuid4()

obshalka_id = uuid.uuid4()
translator_id = uuid.uuid4()
adecvater_id = uuid.uuid4()
luchi_id = uuid.uuid4()
otezd_id = uuid.uuid4()
prss_relise = uuid.uuid4()
comments_id = uuid.uuid4()
statyi_id = uuid.uuid4()
anticrisis_comments_id = uuid.uuid4()
rewrite_id = uuid.uuid4()
public_speech_id = uuid.uuid4()
plan_statyi_id = uuid.uuid4()

files = {obshalka_id: '1.1 Общалка САЙТ-2.txt',
         translator_id: '1.2 Переводчик САЙТ-2.txt',
         adecvater_id: '1.3 Адекватизатор САЙТ-2.txt',
         luchi_id: '1.4 Лучи поддержки САЙТ-2.txt',
         otezd_id: '1.5 Грамотная отъезд САЙТ.txt',
         prss_relise: '2.1 Пресс-релизы САЙТ.txt',
         comments_id: '2.2 Комментарии СМИ САЙТ.txt',
         statyi_id: '2.4 Статьи БЕТА-ТЕСТ САЙТ.txt',
         plan_statyi_id: '2.5 План статьи САЙТ.txt',
         rewrite_id: '2.6 Рерайты САЙТ.txt',
         anticrisis_comments_id: '2_3_Антикризисные_комментарии_СМИ_САЙТ.txt',
         public_speech_id: '2_7_Публичные_речи_для_руководства_САЙТ.txt'}


async def add_category(session, category_id):
    with open('/home/vladimir/PycharmProjects/Pyaroshnaya-backend/venv/' + files[category_id]) as f:
        data = json.load(f)

    questions = data['questions']
    question_models = []
    options = []
    for i, q in enumerate(questions):
        question_models.append(Question(id=(question_id := uuid.uuid4()),
                                        is_required=(req := not q['question'].startswith('ОПЦИОНАЛЬНО: ')),
                                        question_text=q['question'] if req else q['question'][13:],
                                        category_id=category_id, order_index=str(i), snippet=q.get('snippet'),
                                        type_=q['type']))
        if q['type'] == 'options':
            options.extend([Option(id=option['id'], question_id=question_id, option_text=option['text'],
                                   text_to_prompt=option['prompt_text']) for option in q['options']])

    prompt_texts = data['prompt'][1:]
    session.add_all(question_models)
    await session.flush()
    if options != []:
        session.add_all(options)
    session.add_all(
        [Prompt(id=uuid.uuid4(), category_id=category_id, text=prompt_text, order_index=str(i)) for i, prompt_text in
         enumerate(prompt_texts)])


async def main():
    async with async_session_maker.begin() as session:

        session.add(Category(id=first_id,
                             title='Общечеловеческие ценности 🙂',
                             is_category_screen_presented=True,
                             is_main_screen_presented=False,
                             order_index='1',
                             description='За доступ к высоким технологиям не всегда нужно платить! Тем более, если вы только знакомитесь с нейронными сетями и хотите изучить их способности   Попробуйте задать вопросы ИИ в разделе «Общалка», закиньте любой текст в «Переводчик» или зайдите в шуточные разделы с отмазками или лучами поддержки.'))
        await session.flush()
        session.add(Category(id=obshalka_id,
                             title='Общалка',
                             is_category_screen_presented=True,
                             is_main_screen_presented=False,
                             order_index='1.1',
                             description='В «Общалке» вы можете задать нейросети совершенно любой вопрос. Как добраться из Питера в Казань без самолетов и поездов. Как организовать 3х дневную поездку в Стамбул так, чтобы не упустить ни одной достопримечательности. В чем различия между машинами Volkswagen Touareg и Skoda Kodiak, и какая из них лучше подойдет для жизни в пригороде мегаполиса? Как научиться плавать кролем – с подробным планом тренировок? Вопросы – ограничены лишь вашей фантазией\nЕдинственное, учтите, что наш ИИ сейчас работает в режиме «вопрос-ответ», и не будет помнить контекст предыдущего диалога, а также не очень хорошо ориентируется в последних мировых событиях и ценах. Зато умный – сил нет )',
                             parent_id=first_id))
        session.add(Category(id=translator_id,
                             title='Переводчик',
                             is_category_screen_presented=True,
                             is_main_screen_presented=False,
                             order_index='1.2',
                             description='Переводите любые тексты с любых языков! С русского на английский? Легко! С испанского на французский? Тоже элементарно  А с помощью настроек художественности или деловой переписки – вы сможете более четко выбрать желаемый образ результата.\nИ помните – если первая версия текста вас не устроила – смело повторяйте генерацию до тех пор, пока не получите нужный результат. Обычно требуется 2-4 нажатия. Количество генераций – не ограничено )',
                             parent_id=first_id))
        session.add(Category(id=adecvater_id,
                             title='Адекватезатор',
                             is_category_screen_presented=True,
                             is_main_screen_presented=False,
                             order_index='1.3',
                             description='Маркетологи прислали текст, от которого скрипят зубы? Копирайтер перепил смузи и текст получился излишне ванильным? Адекватизатор попробует сделать материал… более адекватным  Дополнительные указания – что на выходе текст должен быть для внутрикома, или для листовок в магазине – значительно упросят задачу ИИ.',
                             parent_id=first_id))
        session.add(Category(id=luchi_id,
                             title='Лучи поддержки',
                             is_category_screen_presented=True,
                             is_main_screen_presented=False,
                             order_index='1.4',
                             description='Проблемы на работе? Все надоели? Кот съел любимый цветок и раздраконил обои?\nнам иногда нужна поддержка! Просто вбейте имя, и «Пярошная» постарается вас подбодрить',
                             parent_id=first_id))
        session.add(Category(id=otezd_id,
                             title='Грамотный отъезд',
                             is_category_screen_presented=True,
                             is_main_screen_presented=False,
                             order_index='1.5',
                             description='Опоздали на работу? Забыли ноутбук в тайланде? Лень написать деловое письмо?\nМы поможем «отъехать» с проблемки',
                             parent_id=first_id))

        session.add(Category(id=second_id,
                             title='Работа со СМИ',
                             is_category_screen_presented=False,
                             is_main_screen_presented=False,
                             order_index='2',
                             description='В этом разделе собраны инструменты, нужные специалистам по работе со СМИ. Ключевые материалы при общении с журналистами: пресс-релизы, комментарии, антикризисные коммуникации, рерайты.\nНекоторые задачи, как стратегии, еще находятся в режиме теста, но их тоже можно попробовать ради интереса'))
        await session.flush()
        session.add(Category(id=prss_relise,
                             title='Пресс-Релизы',
                             is_category_screen_presented=False,
                             is_main_screen_presented=False,
                             order_index='2.1',
                             description='',
                             parent_id=second_id))
        session.add(Category(id=comments_id,
                             title='Комментарии',
                             is_category_screen_presented=False,
                             is_main_screen_presented=False,
                             order_index='2.2',
                             description='',
                             parent_id=second_id))
        session.add(Category(id=anticrisis_comments_id,
                             title='Антикризисные комментарии',
                             is_category_screen_presented=False,
                             is_main_screen_presented=False,
                             order_index='2.3',
                             description='',
                             parent_id=second_id))
        session.add(Category(id=statyi_id,
                             title='Статьи',
                             is_category_screen_presented=False,
                             is_main_screen_presented=False,
                             order_index='2.4',
                             description='',
                             parent_id=second_id))
        session.add(Category(id=plan_statyi_id,
                             title='Планы статей',
                             is_category_screen_presented=False,
                             is_main_screen_presented=False,
                             order_index='2.5',
                             description='',
                             parent_id=second_id))
        session.add(Category(id=rewrite_id,
                             title='Рерайты',
                             is_category_screen_presented=False,
                             is_main_screen_presented=False,
                             order_index='2.6',
                             description='',
                             parent_id=second_id))
        session.add(Category(id=public_speech_id,
                             title='',
                             is_category_screen_presented=False,
                             is_main_screen_presented=False,
                             order_index='2.7',
                             description='',
                             parent_id=second_id))
        session.add(Category(id=third_id,
                             title='Работа с соцмедиа',
                             is_main_screen_presented=False,
                             is_category_screen_presented=True,
                             order_index='3',
                             description=''))
        await session.flush()
        session.add(Category(id=uuid.uuid4(),
                             title='Посты в ТГ-канал',
                             is_main_screen_presented=False,
                             is_category_screen_presented=True,
                             order_index='3.1',
                             description='',
                             parent_id=third_id))
        session.add(Category(id=uuid.uuid4(),
                             title='Посты в ФБ',
                             is_main_screen_presented=False,
                             is_category_screen_presented=True,
                             order_index='3.2',
                             description='',
                             parent_id=third_id))
        session.add(Category(id=uuid.uuid4(),
                             title='Посты в ВК',
                             is_main_screen_presented=False,
                             is_category_screen_presented=True,
                             order_index='3.3',
                             description='',
                             parent_id=third_id))
        session.add(Category(id=uuid.uuid4(),
                             title='Посты в Instagram',
                             is_main_screen_presented=False,
                             is_category_screen_presented=True,
                             order_index='3.4',
                             description='',
                             parent_id=third_id))
        session.add(Category(id=uuid.uuid4(),
                             title='Темплан для соцмедиа',
                             is_main_screen_presented=False,
                             is_category_screen_presented=True,
                             order_index='3.5',
                             description='',
                             parent_id=third_id))
        session.add(Category(id=uuid.uuid4(),
                             title='Работа с отзывами',
                             is_main_screen_presented=False,
                             is_category_screen_presented=True,
                             order_index='3.6',
                             description='',
                             parent_id=third_id))

        session.add(Category(id=fourth_id,
                             title='Внутренние коммуникации и корпкультура',
                             is_main_screen_presented=False,
                             is_category_screen_presented=False,
                             order_index='4',
                             description=''))
        await session.flush()
        session.add(Category(id=uuid.uuid4(),
                             title='Внутриком Рассылки',
                             is_main_screen_presented=False,
                             is_category_screen_presented=False,
                             order_index='4.1',
                             description='',
                             parent_id=fourth_id))
        session.add(Category(id=uuid.uuid4(),
                             title='Внутриком Антикризис',
                             is_main_screen_presented=False,
                             is_category_screen_presented=False,
                             order_index='4.2',
                             description='',
                             parent_id=fourth_id))
        session.add(Category(id=uuid.uuid4(),
                             title='Внутренние речи для руководства',
                             is_main_screen_presented=False,
                             is_category_screen_presented=False,
                             order_index='4.3',
                             description='',
                             parent_id=fourth_id))
        session.add(Category(id=uuid.uuid4(),
                             title='Стратегии ВК',
                             is_main_screen_presented=False,
                             is_category_screen_presented=False,
                             order_index='4.4',
                             description='',
                             parent_id=fourth_id))
        session.add(Category(id=uuid.uuid4(),
                             title='Идеи для подарков/мерча сотрудникам',
                             is_main_screen_presented=False,
                             is_category_screen_presented=False,
                             order_index='4.5',
                             description='',
                             parent_id=fourth_id))
        session.add(Category(id=fifth_id,
                             title='Ивенты',
                             is_main_screen_presented=False,
                             is_category_screen_presented=False,
                             order_index='5',
                             description=''))
        await session.flush()
        session.add(Category(id=uuid.uuid4(),
                             title='Приглашения',
                             is_main_screen_presented=False,
                             is_category_screen_presented=False,
                             order_index='5.1',
                             description='',
                             parent_id=fifth_id))
        session.add(Category(id=uuid.uuid4(),
                             title='POS-брошюры',
                             is_main_screen_presented=False,
                             is_category_screen_presented=False,
                             order_index='5.2',
                             description='',
                             parent_id=fifth_id))
        session.add(Category(id=uuid.uuid4(),
                             title='стратегии - Планирование ивентов',
                             is_main_screen_presented=False,
                             is_category_screen_presented=False,
                             order_index='5.3',
                             description='',
                             parent_id=fifth_id))
        session.add(Category(id=uuid.uuid4(),
                             title='Тексты ведущих',
                             is_main_screen_presented=False,
                             is_category_screen_presented=False,
                             order_index='5.4',
                             description='',
                             parent_id=fifth_id))
        await session.flush()

        await add_category(session, obshalka_id)
        await add_category(session, translator_id)
        await add_category(session, adecvater_id)
        await add_category(session, luchi_id)
        await add_category(session, otezd_id)
        await add_category(session, prss_relise)
        await add_category(session, comments_id)
        await add_category(session, statyi_id)
        await add_category(session, rewrite_id)
        await add_category(session, anticrisis_comments_id)
        await add_category(session, public_speech_id)


        # with open('/home/vladimir/PycharmProjects/Pyaroshnaya-backend/venv/1.2 Переводчик САЙТ-2.txt') as f:
        #     data = json.load(f)
        #
        # questions = data['questions']
        # session.add_all([Question(id=uuid.uuid4(), is_required=(req:=not q['question'].startswith('ОПЦИОНАЛЬНО: ')), question_text=q['question'] if req else q['question'][13:],
        #                           category_id=translator_id, order_index=str(i), snippet=q.get('snippet')) for i,q in enumerate(questions)])
        # prompt_texts = data['prompt'][1:]
        # session.add_all([Prompt(id=uuid.uuid4(), category_id=translator_id, text=prompt_text, order_index=str(i)) for i, prompt_text in enumerate(prompt_texts)])
        #
        #
        # with open('/home/vladimir/PycharmProjects/Pyaroshnaya-backend/venv/1.3 Адекватизатор САЙТ-2.txt') as f:
        #     data = json.load(f)
        #
        # questions = data['questions']
        # session.add_all([Question(id=uuid.uuid4(), is_required=(req:=not q['question'].startswith('ОПЦИОНАЛЬНО: ')), question_text=q['question'] if req else q['question'][13:],
        #                           category_id=adecvater_id, order_index=str(i), snippet=q.get('snippet')) for i,q in enumerate(questions)])
        # prompt_texts = data['prompt'][1:]
        # session.add_all([Prompt(id=uuid.uuid4(), category_id=adecvater_id, text=prompt_text, order_index=str(i)) for i, prompt_text in enumerate(prompt_texts)])
        #
        #
        # with open('/home/vladimir/PycharmProjects/Pyaroshnaya-backend/venv/1.4 Лучи поддержки САЙТ-2.txt') as f:
        #     data = json.load(f)
        #
        # questions = data['questions']
        # session.add_all([Question(id=uuid.uuid4(), is_required=(req:=not q['question'].startswith('ОПЦИОНАЛЬНО: ')), question_text=q['question'] if req else q['question'][13:],
        #                           category_id=luchi_id, order_index=str(i), snippet=q.get('snippet')) for i,q in enumerate(questions)])
        # prompt_texts = data['prompt'][1:]
        # session.add_all([Prompt(id=uuid.uuid4(), category_id=luchi_id, text=prompt_text, order_index=str(i)) for i, prompt_text in enumerate(prompt_texts)])
        #
        # with open('/home/vladimir/PycharmProjects/Pyaroshnaya-backend/venv/1.5 Грамотная отъезд САЙТ.txt') as f:
        #     data = json.load(f)
        #
        # questions = data['questions']
        # session.add_all([Question(id=uuid.uuid4(), is_required=(req:=not q['question'].startswith('ОПЦИОНАЛЬНО: ')), question_text=q['question'] if req else q['question'][13:],
        #                           category_id=otezd_id, order_index=str(i), snippet=q.get('snippet')) for i,q in enumerate(questions)])
        # prompt_texts = data['prompt'][1:]
        # session.add_all([Prompt(id=uuid.uuid4(), category_id=otezd_id, text=prompt_text, order_index=str(i)) for i, prompt_text in enumerate(prompt_texts)])
        #
        #
        # with open('/home/vladimir/PycharmProjects/Pyaroshnaya-backend/venv/2.1 Пресс-релизы САЙТ.txt') as f:
        #     data = json.load(f)
        #
        # questions = data['questions']
        # session.add_all([Question(id=uuid.uuid4(), is_required=(req:=not q['question'].startswith('ОПЦИОНАЛЬНО: ')), question_text=q['question'] if req else q['question'][13:],
        #                           category_id=prss_relise, order_index=str(i), snippet=q.get('snippet')) for i,q in enumerate(questions)])
        # prompt_texts = data['prompt'][1:]
        # session.add_all([Prompt(id=uuid.uuid4(), category_id=prss_relise, text=prompt_text, order_index=str(i)) for i, prompt_text in enumerate(prompt_texts)])
        #
        #
        # with open('/home/vladimir/PycharmProjects/Pyaroshnaya-backend/venv/2.2 Комментарии СМИ САЙТ.txt') as f:
        #     data = json.load(f)
        #
        # questions = data['questions']
        # session.add_all([Question(id=uuid.uuid4(), is_required=(req:=not q['question'].startswith('ОПЦИОНАЛЬНО: ')), question_text=q['question'] if req else q['question'][13:],
        #                           category_id=comments_id, order_index=str(i), snippet=q.get('snippet')) for i,q in enumerate(questions)])
        # prompt_texts = data['prompt'][1:]
        # session.add_all([Prompt(id=uuid.uuid4(), category_id=comments_id, text=prompt_text, order_index=str(i)) for i, prompt_text in enumerate(prompt_texts)])
        #
        #
        # with open('/home/vladimir/PycharmProjects/Pyaroshnaya-backend/venv/2.4 Статьи БЕТА-ТЕСТ САЙТ.txt') as f:
        #     data = json.load(f)
        #
        # questions = data['questions']
        # session.add_all([Question(id=uuid.uuid4(), is_required=(req:=not q['question'].startswith('ОПЦИОНАЛЬНО: ')), question_text=q['question'] if req else q['question'][13:],
        #                           category_id=statyi_id, order_index=str(i), snippet=q.get('snippet')) for i,q in enumerate(questions)])
        # prompt_texts = data['prompt'][1:]
        # session.add_all([Prompt(id=uuid.uuid4(), category_id=statyi_id, text=prompt_text, order_index=str(i)) for i, prompt_text in enumerate(prompt_texts)])
        #
        #
        # with open('/home/vladimir/PycharmProjects/Pyaroshnaya-backend/venv/2.6 Рерайты САЙТ.txt') as f:
        #     data = json.load(f)
        #
        #
        # with open('/home/vladimir/PycharmProjects/Pyaroshnaya-backend/venv/2.4 Статьи БЕТА-ТЕСТ САЙТ.txt') as f:
        #     data = json.load(f)
        #
        # questions = data['questions']
        # session.add_all([Question(id=uuid.uuid4(), is_required=(req:=not q['question'].startswith('ОПЦИОНАЛЬНО: ')), question_text=q['question'] if req else q['question'][13:],
        #                           category_id=statyi_id, order_index=str(i), snippet=q.get('snippet')) for i,q in enumerate(questions)])
        # prompt_texts = data['prompt'][1:]
        # session.add_all([Prompt(id=uuid.uuid4(), category_id=statyi_id, text=prompt_text, order_index=str(i)) for i, prompt_text in enumerate(prompt_texts)])
        #
        #
        # with open('/home/vladimir/PycharmProjects/Pyaroshnaya-backend/venv/2.5 План статьи САЙТ.txt') as f:
        #     data = json.load(f)
        #
        # questions = data['questions']
        # session.add_all([Question(id=uuid.uuid4(), is_required=(req:=not q['question'].startswith('ОПЦИОНАЛЬНО: ')), question_text=q['question'] if req else q['question'][13:],
        #                           category_id=plan_statyi_id, order_index=str(i), snippet=q.get('snippet')) for i,q in enumerate(questions)])
        # prompt_texts = data['prompt'][1:]
        # session.add_all([Prompt(id=uuid.uuid4(), category_id=plan_statyi_id, text=prompt_text, order_index=str(i)) for i, prompt_text in enumerate(prompt_texts)])
        #
        #
        # with open('/home/vladimir/PycharmProjects/Pyaroshnaya-backend/venv/2.6 Рерайты САЙТ.txt') as f:
        #     data = json.load(f)
        #
        # questions = data['questions']
        # session.add_all([Question(id=uuid.uuid4(), is_required=(req:=not q['question'].startswith('ОПЦИОНАЛЬНО: ')), question_text=q['question'] if req else q['question'][13:],
        #                           category_id=rewrite_id, order_index=str(i), snippet=q.get('snippet')) for i,q in enumerate(questions)])
        # prompt_texts = data['prompt'][1:]
        # session.add_all([Prompt(id=uuid.uuid4(), category_id=rewrite_id, text=prompt_text, order_index=str(i)) for i, prompt_text in enumerate(prompt_texts)])
        #
        #
        # with open('/home/vladimir/PycharmProjects/Pyaroshnaya-backend/venv/2_3_Антикризисные_комментарии_СМИ_САЙТ.txt') as f:
        #     data = json.load(f)
        #
        # questions = data['questions']
        # session.add_all([Question(id=uuid.uuid4(), is_required=(req:=not q['question'].startswith('ОПЦИОНАЛЬНО: ')), question_text=q['question'] if req else q['question'][13:],
        #                           category_id=anticrisis_comments_id, order_index=str(i), snippet=q.get('snippet')) for i,q in enumerate(questions)])
        # prompt_texts = data['prompt'][1:]
        # session.add_all([Prompt(id=uuid.uuid4(), category_id=anticrisis_comments_id, text=prompt_text, order_index=str(i)) for i, prompt_text in enumerate(prompt_texts)])
        #
        #
        # with open('/home/vladimir/PycharmProjects/Pyaroshnaya-backend/venv/2_7_Публичные_речи_для_руководства_САЙТ.txt') as f:
        #     data = json.load(f)
        #
        # questions = data['questions']
        # session.add_all([Question(id=uuid.uuid4(), is_required=(req:=not q['question'].startswith('ОПЦИОНАЛЬНО: ')), question_text=q['question'] if req else q['question'][13:],
        #                           category_id=public_speech_id, order_index=str(i), snippet=q.get('snippet')) for i,q in enumerate(questions)])
        # prompt_texts = data['prompt'][1:]
        # session.add_all([Prompt(id=uuid.uuid4(), category_id=public_speech_id, text=prompt_text, order_index=str(i)) for i, prompt_text in enumerate(prompt_texts)])

asyncio.run(main())
