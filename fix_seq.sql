SELECT setval('clientes_id_seq', (SELECT MAX(id) FROM clientes));
