// View (MVC): interface que consome a API Python.
const $ = (id) => document.getElementById(id);
let modoCadastro = false;
let horaEscolhida = null;

async function api(url, metodo = "GET", corpo) {
  const r = await fetch(url, {
    method: metodo,
    headers: { "Content-Type": "application/json" },
    body: corpo ? JSON.stringify(corpo) : undefined,
  });
  const dados = await r.json().catch(() => ({}));
  if (!r.ok) throw new Error(dados.erro || "Erro inesperado.");
  return dados;
}

function aviso(texto, ok = false) {
  $("msg").textContent = texto;
  $("msg").className = texto ? (ok ? "ok" : "erro") : "";
}

function alternarModo() {
  document.querySelectorAll(".so-cadastro").forEach((e) => (e.hidden = !modoCadastro));
  $("auth-titulo").textContent = modoCadastro ? "Criar conta" : "Entrar";
  $("alternar").textContent = modoCadastro ? "Já tem conta? Entrar" : "Não tem conta? Cadastre-se";
}

function mostrarApp(usuario) {
  $("auth").hidden = !!usuario;
  $("app").hidden = !usuario;
  $("nav").hidden = !usuario;
  if (usuario) {
    $("saudacao").textContent = "Olá, " + usuario.nome;
    carregarLista();
  }
}

async function carregarServicos() {
  const lista = await api("/api/servicos");
  $("servico").replaceChildren(...lista.map((s) => new Option(`${s.nome} (${s.duracao} min)`, s.id)));
}

async function carregarHorarios() {
  horaEscolhida = null;
  $("horarios").replaceChildren();
  if (!$("data").value) return;
  try {
    const horas = await api("/api/horarios?data=" + $("data").value);
    horas.forEach((h) => {
      const b = document.createElement("button");
      b.textContent = h.hora;
      b.disabled = !h.livre;
      b.onclick = () => {
        horaEscolhida = h.hora;
        document.querySelectorAll("#horarios button").forEach((x) => x.classList.remove("sel"));
        b.classList.add("sel");
      };
      $("horarios").append(b);
    });
  } catch (e) { aviso(e.message); }
}

async function carregarLista() {
  const itens = await api("/api/agendamentos");
  $("lista").replaceChildren(...itens.map((a) => {
    const li = document.createElement("li");
    const [ano, mes, dia] = a.data.split("-");
    const span = document.createElement("span");
    span.textContent = `${dia}/${mes}/${ano} às ${a.hora} · ${a.servico}`;
    const b = document.createElement("button");
    b.textContent = "Cancelar";
    b.onclick = async () => {
      if (!confirm("Cancelar este agendamento?")) return;
      try { await api("/api/agendamentos/" + a.id, "DELETE"); aviso("Agendamento cancelado.", true); carregarLista(); carregarHorarios(); }
      catch (e) { aviso(e.message); }
    };
    li.append(span, b);
    return li;
  }));
}

$("alternar").onclick = (e) => { e.preventDefault(); modoCadastro = !modoCadastro; alternarModo(); aviso(""); };

$("form-auth").onsubmit = async (e) => {
  e.preventDefault();
  const corpo = { email: $("email").value, senha: $("senha").value };
  if (modoCadastro) { corpo.nome = $("nome").value; corpo.telefone = $("telefone").value; }
  try {
    const u = await api(modoCadastro ? "/api/cadastro" : "/api/login", "POST", corpo);
    aviso("");
    mostrarApp(u);
  } catch (err) { aviso(err.message); }
};

$("sair").onclick = async () => { await api("/api/logout", "POST"); mostrarApp(null); };

$("data").onchange = carregarHorarios;

$("agendar").onclick = async () => {
  if (!$("data").value || !horaEscolhida) return aviso("Escolha a data e o horário.");
  try {
    await api("/api/agendamentos", "POST", { servico_id: Number($("servico").value), data: $("data").value, hora: horaEscolhida });
    aviso("Agendamento confirmado!", true);
    carregarLista();
    carregarHorarios();
  } catch (err) { aviso(err.message); carregarHorarios(); }
};

(async () => {
  alternarModo();
  $("data").min = new Date().toISOString().slice(0, 10);
  await carregarServicos();
  try { mostrarApp(await api("/api/me")); } catch { mostrarApp(null); }
})();
