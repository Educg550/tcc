# senhaunica

O sistema **senhaunica** é responsável pela autorização e acesso a recursos baseado no protocolo **Oauth 1.0**[^1] da RFC5849[^2].

As suas configurações de ambiente padrões para o desenvolvimento são:

```ini
OAUTH_HOST=https://dev.uspdigital.usp.br
REQUEST_TOKEN_RESOURCE=wsusuario/oauth/access_token
AUTHORIZE_URL=wsusuario/oauth/authorize
ACCESS_TOKEN_RESOURCE=wsusuario/oauth/request_token
```

[^1]: embora o protocolo seja considerado obsoleto
[^2]: https://datatracker.ietf.org/doc/html/rfc5849