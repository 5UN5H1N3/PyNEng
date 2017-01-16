#Обработка вывода команд с TextFSM

Мы уже научились работать с разными структурами данных Python и разобрались с несколькими модулями, полезными для работы с сетевым оборудованием. И, хотя мы уже можем отправлять команды на оборудование и генерировать шаблоны конфигураций, не хватает одного важного аспекта: получение структурированного вывода с оборудования.

Как правило, вывод это результат выполнения команд show. Было бы хорошо, если бы мы могли получить вывод команды show, например, в формате JSON, или YAML, или XML. Или, хотя бы в виде списка или словаря Python.

Но, к сожалению, на оборудовании, которое не поддерживает какого-то программного интерфейса, мы получаем вывод просто как строку. Конечно, отчасти она структурирована, и этим мы воспользуемся, но всё же это просто строка. И нам надо как-то обработать её, чтобы получить объекты Python, например, словарь или список.

Простого способа для этого нет. Но есть более удобный вариант, чем просто обрабатывать каждый вывод построчно: TextFSM.

> Использование TextFSM лучше, чем простая построчная обработка, так как шаблоны дают лучшее представление о том, как вывод будет обрабатываться и шаблонами проще поделиться. А значит, проще найти уже созданные шаблоны и использовать их. Или поделиться своими.

TextFSM это библиотека созданная Google как раз для обработки такого вывода с сетевых устройств.

Для начала, библиотеку надо установить:
```
pip install gtextfsm
```

Для того, чтобы мы могли её использовать, нам надо создать шаблон, по которому будет обрабатываться вывод команды и сам вывод команды.

Для примера, возьмем вывод команды traceroute:
```
r2#traceroute 90.0.0.9 source 33.0.0.2
traceroute 90.0.0.9 source 33.0.0.2
Type escape sequence to abort.
Tracing the route to 90.0.0.9
VRF info: (vrf in name/id, vrf out name/id)
  1 10.0.12.1 1 msec 0 msec 0 msec
  2 15.0.0.5  0 msec 5 msec 4 msec
  3 57.0.0.7  4 msec 1 msec 4 msec
  4 79.0.0.9  4 msec *  1 msec
```

В данном случае нас интересуют только хопы, через которые прошел пакет. То есть, мы считаем, что отправитель и получатель нам и так известны и их не надо получать из вывода команды traceroute.

В таком случае, шаблон TextFSM будет выглядеть так (файл traceroute.template):
```
Value ID (\d+)
Value Hop (\d+(\.\d+){3})

Start
  ^  ${ID} ${Hop} -> Record
```

Первые две строки определяют переменные:
* ```Value ID (\d+)``` - эта строка определяет переменную ID, которая описывает регулярное выражение: ```(\d+)``` - одна или более цифр
 * сюда попадут номера хопов
* ```Value Hop (\d+(\.\d+){3})``` - эта строка определяет переменную Hop, которая описывает IP-адрес таким регулярным выражением: ```(\d+(\.\d+){3})```

После строки Start начинается сам шаблон. В данном случае, он очень простой:
* ```^  ${ID} ${Hop} -> Record```
 * сначала идет символ начала строки, затем два пробела и переменные ID и Hop
 * в TextFSM переменные описываются таким образом: ${имя переменной}
 * слово Record в конце означает, что строки, которые попадут под описанный шаблон, будут обработаны и выведены в результаты TextFSM (с этим подробнее мы разберемся позже)

Теперь посмотрим как выглядит скрипт обработки вывода команды traceroute с помощью TextFSM (parse_traceroute.py):
```python
import textfsm

traceroute = """
r2#traceroute 90.0.0.9 source 33.0.0.2
traceroute 90.0.0.9 source 33.0.0.2
Type escape sequence to abort.
Tracing the route to 90.0.0.9
VRF info: (vrf in name/id, vrf out name/id)
  1 10.0.12.1 1 msec 0 msec 0 msec
  2 15.0.0.5  0 msec 5 msec 4 msec
  3 57.0.0.7  4 msec 1 msec 4 msec
  4 79.0.0.9  4 msec *  1 msec
"""

template = open('traceroute.textfsm')
fsm = textfsm.TextFSM(template)
result = fsm.ParseText(traceroute)

print fsm.header
print result
```

Сначала посмотрим на вывод скрипта, а затем разберемся со скриптом:
```
['ID', 'Hop']
[['1', '10.0.12.1'], ['2', '15.0.0.5'], ['3', '57.0.0.7'], ['4', '79.0.0.9']]
```

Мы получили все строки, которые совпали с описанным шаблоном, в виде списка. Внутри, каждый элемент тоже список, который состоит из двух элементов: номера хопа и IP-адреса.

Разберемся с содержимым скрипта:
* traceroute - это переменная, которая содержит вывод команды traceroute
* ```template = open('traceroute.textfsm')``` - мы считываем содержимое файла с шаблоном TextFSM в переменную template
* ```fsm = textfsm.TextFSM(template)``` - класс, который обрабатывает шаблон и создает из него объект в TextFSM
* ```result = fsm.ParseText(traceroute)``` - метод, который обрабатывает переданный вывод согласно шаблону и возращает список списков. В котором каждый элемент это обработанная строка
* В конце мы выводим заголовок - имена переменных и результат обработки

Теперь у нас есть вывод в виде списка и мы можем, например, периодически выполнять команду traceroute и сравнивать изменилось ли количество хопов и их порядок.

Далее мы подробнее разберемся с синтаксисом шаблонов, а пока подытожим:
* для работы с TextFSM нужны: вывод команды и шаблон
* для разных команд нужны разные шаблоны
* TextFSM возвращает результат обработки в табличном виде (в виде списка списков)
 * этот вывод легко преобразовать в csv формат или в список словарей (это мы будем делать в упражнениях)