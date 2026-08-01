"""
ORM da Etapa 2 (item 4) — SQLAlchemy 2.0.

Mapeia o schema para classes e declara os relacionamentos usados
pela camada de operações (crud_orm.py). Os enums do Postgres são
mapeados como str (o driver faz o cast), e UUID volta como str para
casar com os UUIDs de seed.
"""
import os
import uuid

from sqlalchemy import (
    create_engine, ForeignKey, String, Integer, Numeric, Text, DateTime, Boolean,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import (
    DeclarativeBase, Mapped, mapped_column, relationship, sessionmaker,
)


def _sqlalchemy_url() -> str:
    """Converte o DSN psycopg2 (`dbname=... user=...`) usado no resto do
    projeto para uma URL SQLAlchemy. Aceita SQLALCHEMY_URL direto se existir."""
    direto = os.getenv("SQLALCHEMY_URL")
    if direto:
        return direto
    dsn = os.getenv(
        "DATABASE_URL",
        "dbname=hospital_db user=postgres password=password host=localhost port=5433",
    )
    if dsn.startswith("postgresql://") or dsn.startswith("postgresql+"):
        return dsn
    partes = dict(p.split("=", 1) for p in dsn.split() if "=" in p)
    return (
        f"postgresql+psycopg2://{partes.get('user','postgres')}:"
        f"{partes.get('password','')}@{partes.get('host','localhost')}:"
        f"{partes.get('port','5432')}/{partes.get('dbname','hospital_db')}"
    )


engine = create_engine(_sqlalchemy_url(), future=True)
Session = sessionmaker(bind=engine, future=True, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


_UUID = UUID(as_uuid=False)


class Pessoa(Base):
    __tablename__ = "pessoa"
    id_pessoa: Mapped[str] = mapped_column(_UUID, primary_key=True)
    nome: Mapped[str] = mapped_column(String(150))
    cpf: Mapped[str] = mapped_column(String(11))
    data_nascimento: Mapped[str] = mapped_column(String)  # date; str basta p/ leitura
    is_flamengo: Mapped[bool] = mapped_column(Boolean)
    telefone: Mapped[str | None] = mapped_column(String(20))

    paciente: Mapped["Paciente"] = relationship(back_populates="pessoa", uselist=False)
    profissional: Mapped["Profissional"] = relationship(back_populates="pessoa", uselist=False)


class Paciente(Base):
    __tablename__ = "paciente"
    id_pessoa: Mapped[str] = mapped_column(_UUID, ForeignKey("pessoa.id_pessoa"), primary_key=True)
    num_convenio: Mapped[str | None] = mapped_column(String(50))
    alergias: Mapped[str | None] = mapped_column(Text)
    grupo_sanguineo: Mapped[str | None] = mapped_column(String(3))

    pessoa: Mapped[Pessoa] = relationship(back_populates="paciente")
    atendimentos: Mapped[list["Atendimento"]] = relationship(back_populates="paciente")


class Profissional(Base):
    __tablename__ = "profissional"
    id_pessoa: Mapped[str] = mapped_column(_UUID, ForeignKey("pessoa.id_pessoa"), primary_key=True)
    crm: Mapped[str] = mapped_column(String(20))
    data_admissao: Mapped[str] = mapped_column(String)
    especialidade: Mapped[str] = mapped_column(String(100))
    papel_atual: Mapped[str] = mapped_column(String)

    pessoa: Mapped[Pessoa] = relationship(back_populates="profissional")


class Preceptor(Base):
    __tablename__ = "preceptor"
    id_pessoa: Mapped[str] = mapped_column(_UUID, ForeignKey("profissional.id_pessoa"), primary_key=True)
    papel: Mapped[str] = mapped_column(String)
    titulacao: Mapped[str] = mapped_column(String(50))

    profissional: Mapped[Profissional] = relationship()


class Residente(Base):
    __tablename__ = "residente"
    id_pessoa: Mapped[str] = mapped_column(_UUID, ForeignKey("profissional.id_pessoa"), primary_key=True)
    papel: Mapped[str] = mapped_column(String)
    ano_residencia: Mapped[str] = mapped_column(String)

    profissional: Mapped[Profissional] = relationship()


class Unidade(Base):
    __tablename__ = "unidade"
    id_unidade: Mapped[str] = mapped_column(_UUID, primary_key=True)
    nome: Mapped[str] = mapped_column(String(100))
    tipo: Mapped[str] = mapped_column(String(30))
    capacidade_leitos: Mapped[int] = mapped_column(Integer)


class Procedimento(Base):
    __tablename__ = "procedimento"
    id_procedimento: Mapped[str] = mapped_column(_UUID, primary_key=True)
    codigo: Mapped[str] = mapped_column(String(20))
    nome: Mapped[str] = mapped_column(String(100))
    tempo_medio_minutos: Mapped[int] = mapped_column(Integer)
    nivel_risco: Mapped[str] = mapped_column(String)


class Atendimento(Base):
    __tablename__ = "atendimento"
    id_atendimento: Mapped[str] = mapped_column(_UUID, primary_key=True, default=lambda: str(uuid.uuid4()))
    data_hora: Mapped[str] = mapped_column(DateTime)
    duracao_minutos: Mapped[int] = mapped_column(Integer)
    id_paciente: Mapped[str] = mapped_column(_UUID, ForeignKey("paciente.id_pessoa"))
    id_residente: Mapped[str] = mapped_column(_UUID, ForeignKey("residente.id_pessoa"))
    id_preceptor: Mapped[str] = mapped_column(_UUID, ForeignKey("preceptor.id_pessoa"))
    id_unidade: Mapped[str] = mapped_column(_UUID, ForeignKey("unidade.id_unidade"))

    paciente: Mapped[Paciente] = relationship(back_populates="atendimentos")
    residente: Mapped[Residente] = relationship()
    preceptor: Mapped[Preceptor] = relationship()
    unidade: Mapped[Unidade] = relationship()
    # lazy default (select); crud_orm usa selectinload p/ eager quando precisa.
    procedimentos: Mapped[list["ProcedimentoRealizado"]] = relationship(
        back_populates="atendimento", cascade="all, delete-orphan"
    )


class ProcedimentoRealizado(Base):
    __tablename__ = "procedimento_realizado"
    id_atendimento: Mapped[str] = mapped_column(_UUID, ForeignKey("atendimento.id_atendimento"), primary_key=True)
    id_procedimento: Mapped[str] = mapped_column(_UUID, ForeignKey("procedimento.id_procedimento"), primary_key=True)
    quantidade: Mapped[int] = mapped_column(Integer)
    tempo_real_minutos: Mapped[int] = mapped_column(Integer)
    data_hora_inicio: Mapped[str] = mapped_column(DateTime)
    observacao: Mapped[str | None] = mapped_column(Text)

    atendimento: Mapped[Atendimento] = relationship(back_populates="procedimentos")
    procedimento: Mapped[Procedimento] = relationship()


class Faturamento(Base):
    __tablename__ = "faturamento"
    id_faturamento: Mapped[str] = mapped_column(_UUID, primary_key=True)
    id_atendimento: Mapped[str] = mapped_column(_UUID)
    id_procedimento: Mapped[str] = mapped_column(_UUID)
    valor: Mapped[float] = mapped_column(Numeric(10, 2))
    data_emissao: Mapped[str] = mapped_column(String)


class Escala(Base):
    __tablename__ = "escala"
    id_escala: Mapped[str] = mapped_column(_UUID, primary_key=True, default=lambda: str(uuid.uuid4()))
    id_unidade: Mapped[str] = mapped_column(_UUID, ForeignKey("unidade.id_unidade"))
    dia_semana: Mapped[str] = mapped_column(String)
    turno: Mapped[str] = mapped_column(String)
    id_residente: Mapped[str] = mapped_column(_UUID, ForeignKey("residente.id_pessoa"))
    id_preceptor: Mapped[str] = mapped_column(_UUID, ForeignKey("preceptor.id_pessoa"))

    unidade: Mapped[Unidade] = relationship()
    residente: Mapped[Residente] = relationship()
    preceptor: Mapped[Preceptor] = relationship()