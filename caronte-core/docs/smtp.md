# smtp4dev

Durante o desenvolvimento, é utilizado a ferramenta [smtp4dev](https://github.com/rnwood/smtp4dev) executada em um *container docker*, e as suas configurações de ambiente são[^1]:

```ini
SMTP_SERVER=smtp                    # nome do serviço
SMTP_USER=seu_email@example.com
SMTP_PORT=25
```

# gmail

```ini
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=seu_email@gmail.com
SMTP_PASSWORD=password
SMTP_USE_TLS=SMTP_USE_TLS
```

[^1]: https://github.com/rnwood/smtp4dev/wiki/Configuring-Clients