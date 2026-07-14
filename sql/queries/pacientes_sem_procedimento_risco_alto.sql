-- ============================================================
-- CONSULTA ANALÍTICA 4: Pacientes que nunca realizaram nenhum
-- procedimento de nível de risco 'ALTO'.
-- ============================================================

SELECT p.nome AS paciente, pac.num_convenio
FROM PACIENTE pac
JOIN PESSOA p ON p.id_pessoa = pac.id_pessoa
WHERE NOT EXISTS (
    SELECT 1
    FROM ATENDIMENTO a
    JOIN PROCEDIMENTO_REALIZADO pr ON pr.id_atendimento = a.id_atendimento
    JOIN PROCEDIMENTO proc         ON proc.id_procedimento = pr.id_procedimento
    WHERE a.id_paciente = pac.id_pessoa
      AND proc.nivel_risco = 'ALTO'
)
ORDER BY p.nome;
