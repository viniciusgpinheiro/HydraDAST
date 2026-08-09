const API_URL = 'http://localhost:5050';

export async function iniciarPentest(user, url) {
  const resposta = await fetch(`${API_URL}/scrapping`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      user: user,
      url: url,
    })
  });

  if (!resposta.ok) {
    throw new Error(`Erro ${resposta.status} ao chamar /scrapping`);
  }

  const dadosCriados = await resposta.json();
  console.log('Resposta do servidor:', dadosCriados);
  return dadosCriados;
}
