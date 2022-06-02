from bottle import route, run, template, static_file, request, error, post


@route('/hello/<name>')
def index(name):
    return template('<b>Hello {{name}}</b>!', name=name)


@route('/')
def m():
    return '<h1>This is main Page</h1>' \
           '<div><i>by Alexanderov</i></div>'


@route('/docs/dev/<name>.html')
def docs(name):
    print(name)
    return template("https://bottlepy.org/docs/dev/{{name}}.html", name=name)


@route('/file')
def filer():
    name = request.query.get('name', default="")
    return template("<b>Hello, {{name}}!</b>", name=name)


@route('/login')
def login():
    return '''
        <form action="/login2" method="post">
            Username: <input name="username" type="text" />
            Password: <input name="password" type="password" />
            <input value="Login" type="submit" />
        </form>
    '''


@post('/login2')
def login_post():
    return template("<h1>Logged as {{name}}</h1> wit1h password '{{passw}}'",
                    name=request.forms.get('username'),
                    passw=request.forms['password'])


@route('/user/<id:re:[0-9]*>')
def user(id):
    return "<b>Hello, " + id + "!</b>"


@error(404)
def error_page(error):
    print(error)
    print(type(error))
    body = str(error.body)
    page = body[body.index("'") + 1:body.rindex("'")]
    return template("Page '{{page}}' not pawund", page=page)


run(host='0.0.0.0', port=8080)
