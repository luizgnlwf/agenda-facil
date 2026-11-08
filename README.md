# Agenda Fácil (Projeto Integrador II)

Site de agendamentos. Backend em Python (Flask + SQLite), front-end em HTML/CSS/JavaScript, padrão MVC.

- `models.py` → Model (banco de dados)
- `app.py` → Controller (rotas da API e validações)
- `static/` → View (interface)

## Como executar
```
pip install -r requirements.txt
python app.py        # abra http://127.0.0.1:5000
pytest               # testes automatizados
```
## Melhorias futuras

Sugestões feitas pelos testadores que ainda não foram implementadas:

1. **Confirmação do agendamento por e-mail ou WhatsApp**
   - Pedido: receber um aviso com a data e a hora marcadas, para não esquecer o compromisso.
   - Motivo de não ter sido feito: depende de um serviço externo de envio de mensagens, e a hospedagem gratuita usada (PythonAnywhere) restringe o acesso à internet a partir do servidor.
   - Possível solução: integrar um serviço de e-mail transacional ou a API do WhatsApp Business, usando uma hospedagem sem essa restrição.

2. **Recuperação de senha ("Esqueci minha senha")**
   - Pedido: poder redefinir a senha quando ela for esquecida.
   - Motivo de não ter sido feito: o fluxo normal envia um link de redefinição por e-mail, e isso depende do mesmo serviço de envio descrito acima.
   - Possível solução: gerar um link com prazo de validade, enviá-lo por e-mail e criar a tela de nova senha.