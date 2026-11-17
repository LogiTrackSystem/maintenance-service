-- Esquema de maintenance_db (maintenance-service): SQL generado por 'alembic upgrade head --sql' a partir de alembic/versions.
-- Crea todas las tablas, secuencias y restricciones. No contiene datos.
BEGIN;

CREATE TABLE alembic_version (
    version_num VARCHAR(32) NOT NULL, 
    CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num)
);

-- Running upgrade  -> 9d45a85e70cb

CREATE TABLE intervenciones_mantenimiento (
    id UUID NOT NULL, 
    vehiculo_id UUID NOT NULL, 
    tipo VARCHAR NOT NULL, 
    realizado_en TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    costo NUMERIC(10, 2), 
    taller VARCHAR, 
    kilometraje_en_servicio NUMERIC(10, 2), 
    PRIMARY KEY (id)
);

CREATE INDEX ix_intervenciones_mantenimiento_vehiculo_id ON intervenciones_mantenimiento (vehiculo_id);

CREATE TABLE programas_mantenimiento (
    id UUID NOT NULL, 
    vehiculo_id UUID NOT NULL, 
    tipo VARCHAR NOT NULL, 
    fecha_vencimiento TIMESTAMP WITH TIME ZONE, 
    kilometraje_vencimiento NUMERIC(10, 2), 
    prioridad VARCHAR NOT NULL, 
    creado_en TIMESTAMP WITH TIME ZONE DEFAULT now(), 
    actualizado_en TIMESTAMP WITH TIME ZONE DEFAULT now(), 
    PRIMARY KEY (id)
);

CREATE INDEX ix_programas_mantenimiento_vehiculo_id ON programas_mantenimiento (vehiculo_id);

INSERT INTO alembic_version (version_num) VALUES ('9d45a85e70cb') RETURNING alembic_version.version_num;

COMMIT;

