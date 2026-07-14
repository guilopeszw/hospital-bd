 
UPDATE PACIENTE
SET
    num_convenio    = 'UNIMED-999',   -- :num_convenio
    alergias         = 'Dipirona; Poeira', -- :alergias
    grupo_sanguineo  = 'A+'           -- :grupo_sanguineo
WHERE id_pessoa = 'a1111111-1111-1111-1111-111111111111'  -- :id_paciente
RETURNING id_pessoa, num_convenio, alergias, grupo_sanguineo;
 
