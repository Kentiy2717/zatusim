"""feat: каноническая пара friendships и таблица блокировок blocks

Revision ID: c4d81f0a5b21
Revises: 2a96a2057258
Create Date: 2026-11-04 12:00:00.000000

Миграция переводит таблицу ``friendships`` на хранение одной строки на пару
пользователей (``user_id < friend_id`` + ``initiator_id``) и добавляет
отдельную таблицу ``blocks`` для чёрного списка.

Функциональность заявок в друзья на момент применения миграции ещё не была
выпущена в продакшн, поэтому таблица пересоздаётся без переноса данных.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'c4d81f0a5b21'
down_revision: Union[str, Sequence[str], None] = '2a96a2057258'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

STATUS_ENUM = sa.Enum(
    'PENDING',
    'ACCEPTED',
    'DECLINED',
    name='friendshipstatus',
    native_enum=False,
    length=20,
)


def upgrade() -> None:
    """Пересоздаёт friendships в каноническом виде и добавляет blocks."""

    # --- 1. Старая таблица заявок -------------------------------------------
    op.drop_index(op.f('ix_friendships_user_id'), table_name='friendships')
    op.drop_index(op.f('ix_friendships_friend_id'), table_name='friendships')
    op.drop_index(op.f('ix_friendships_id'), table_name='friendships')
    op.drop_table('friendships')

    # --- 2. Новая таблица связей (одна строка на пару) ----------------------
    op.create_table(
        'friendships',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('friend_id', sa.Integer(), nullable=False),
        sa.Column('initiator_id', sa.Integer(), nullable=False),
        sa.Column('status', STATUS_ENUM, nullable=False),
        sa.Column(
            'created_at',
            sa.DateTime(timezone=True),
            server_default=sa.text('now()'),
            nullable=False,
        ),
        sa.Column(
            'updated_at',
            sa.DateTime(timezone=True),
            server_default=sa.text('now()'),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['friend_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['initiator_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'friend_id', name='uq_friendship_pair'),
        sa.CheckConstraint('user_id < friend_id', name='ck_friendship_canonical_pair'),
    )
    op.create_index(
        op.f('ix_friendships_user_id'), 'friendships', ['user_id'], unique=False
    )
    op.create_index(
        op.f('ix_friendships_friend_id'), 'friendships', ['friend_id'], unique=False
    )
    # Составной индекс под выборку «все связи конкретного пользователя»
    op.create_index(
        'ix_friendships_status_user',
        'friendships',
        ['status', 'user_id', 'friend_id'],
        unique=False,
    )

    # --- 3. Чёрный список ---------------------------------------------------
    op.create_table(
        'blocks',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('blocker_id', sa.Integer(), nullable=False),
        sa.Column('blocked_id', sa.Integer(), nullable=False),
        sa.Column(
            'created_at',
            sa.DateTime(timezone=True),
            server_default=sa.text('now()'),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(['blocker_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['blocked_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('blocker_id', 'blocked_id', name='uq_block_pair'),
        sa.CheckConstraint('blocker_id <> blocked_id', name='ck_block_not_self'),
    )
    op.create_index(
        op.f('ix_blocks_blocker_id'), 'blocks', ['blocker_id'], unique=False
    )
    op.create_index(
        op.f('ix_blocks_blocked_id'), 'blocks', ['blocked_id'], unique=False
    )


def downgrade() -> None:
    """Возвращает прежнюю схему friendships и удаляет blocks."""

    op.drop_index(op.f('ix_blocks_blocked_id'), table_name='blocks')
    op.drop_index(op.f('ix_blocks_blocker_id'), table_name='blocks')
    op.drop_table('blocks')

    op.drop_index('ix_friendships_status_user', table_name='friendships')
    op.drop_index(op.f('ix_friendships_friend_id'), table_name='friendships')
    op.drop_index(op.f('ix_friendships_user_id'), table_name='friendships')
    op.drop_table('friendships')

    op.create_table(
        'friendships',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('friend_id', sa.Integer(), nullable=False),
        sa.Column(
            'status',
            sa.Enum(
                'PENDING',
                'ACCEPTED',
                'DECLINED',
                'BLOCKED',
                name='friendshipstatus',
                native_enum=False,
                length=20,
            ),
            nullable=False,
        ),
        sa.Column(
            'created_at',
            sa.DateTime(timezone=True),
            server_default=sa.text('now()'),
            nullable=False,
        ),
        sa.Column(
            'updated_at',
            sa.DateTime(timezone=True),
            server_default=sa.text('now()'),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(['friend_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'friend_id', name='uq_friendship_user_friend'),
    )
    op.create_index(
        op.f('ix_friendships_friend_id'), 'friendships', ['friend_id'], unique=False
    )
    op.create_index(op.f('ix_friendships_id'), 'friendships', ['id'], unique=False)
    op.create_index(
        op.f('ix_friendships_user_id'), 'friendships', ['user_id'], unique=False
    )
