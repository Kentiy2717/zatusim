import React, { useCallback, useEffect, useState } from 'react';
import {
  ActivityIndicator,
  Image,
  Pressable,
  StyleSheet,
  Text,
  TextInput,
  View,
} from 'react-native';

import {
  BlockItem,
  Friendship,
  RelationBrief,
  UserSearchItem,
  UserShort,
  friendsApi,
  getApiError,
  getMediaUrl,
} from '../api/client';

type Tab = 'friends' | 'incoming' | 'outgoing' | 'blocks';

const TABS: { key: Tab; label: string }[] = [
  { key: 'friends', label: 'Друзья' },
  { key: 'incoming', label: 'Входящие' },
  { key: 'outgoing', label: 'Исходящие' },
  { key: 'blocks', label: 'Чёрный список' },
];

/** Кнопка действия в выдаче поиска — зависит от состояния связи. */
function getSearchAction(relation: RelationBrief | null) {
  if (!relation) return { label: 'Добавить в друзья', kind: 'primary' as const };
  if (relation.is_friend) return { label: 'В друзьях', kind: 'muted' as const };
  if (relation.is_incoming_request)
    return { label: 'Принять заявку', kind: 'primary' as const };
  if (relation.is_outgoing_request)
    return { label: 'Отменить заявку', kind: 'ghost' as const };
  if (relation.is_declined) return { label: 'Заявка отклонена', kind: 'muted' as const };
  if (relation.is_blocked_by_me) return { label: 'Разблокировать', kind: 'ghost' as const };
  if (relation.is_blocked_me) return { label: 'Недоступен', kind: 'muted' as const };
  return { label: 'Добавить в друзья', kind: 'primary' as const };
}

function Avatar({ user, size = 48 }: { user: UserShort; size?: number }) {
  const uri = getMediaUrl(user.avatar_url);
  return uri ? (
    <Image source={{ uri }} style={[styles.avatar, { width: size, height: size }]} />
  ) : (
    <View style={[styles.avatarPlaceholder, { width: size, height: size }]}>
      <Text style={[styles.avatarEmoji, { fontSize: size / 2.2 }]}>
        {user.first_name?.charAt(0)?.toUpperCase() || '?'}
      </Text>
    </View>
  );
}

export default function FriendsScreen() {
  const [tab, setTab] = useState<Tab>('friends');

  const [friends, setFriends] = useState<Friendship[]>([]);
  const [incoming, setIncoming] = useState<Friendship[]>([]);
  const [outgoing, setOutgoing] = useState<Friendship[]>([]);
  const [blocks, setBlocks] = useState<BlockItem[]>([]);

  const [query, setQuery] = useState('');
  const [searchResults, setSearchResults] = useState<UserSearchItem[] | null>(null);
  const [searching, setSearching] = useState(false);

  const [loading, setLoading] = useState(true);
  const [pendingId, setPendingId] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [f, i, o, b] = await Promise.all([
        friendsApi.list(),
        friendsApi.incoming(),
        friendsApi.outgoing(),
        friendsApi.blocks(),
      ]);
      setFriends(f.data);
      setIncoming(i.data);
      setOutgoing(o.data);
      setBlocks(b.data);
    } catch (e) {
      setError(getApiError(e, 'Не удалось загрузить список друзей'));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  const run = async (id: number | null, action: () => Promise<unknown>) => {
    setPendingId(id);
    setError(null);
    try {
      await action();
      await load();
      if (searchResults) {
        // обновляем состояния связей в выдаче поиска
        const fresh = await friendsApi.search(query);
        setSearchResults(fresh.data);
      }
    } catch (e) {
      setError(getApiError(e, 'Действие не выполнено'));
    } finally {
      setPendingId(null);
    }
  };

  const handleSearch = async () => {
    const q = query.trim();
    if (q.length < 2) {
      setError('Введите минимум 2 символа для поиска');
      return;
    }
    setSearching(true);
    setError(null);
    try {
      const res = await friendsApi.search(q);
      setSearchResults(res.data);
    } catch (e) {
      setError(getApiError(e, 'Ошибка поиска'));
    } finally {
      setSearching(false);
    }
  };

  const handleSearchAction = (item: UserSearchItem) => {
    const rel = item.relation;
    if (!rel) return run(item.id, () => friendsApi.send({ user_id: item.id }));
    if (rel.is_incoming_request && rel.friendship_id) {
      return run(item.id, () => friendsApi.accept(rel.friendship_id as number));
    }
    if (rel.is_outgoing_request && rel.friendship_id) {
      return run(item.id, () => friendsApi.cancel(rel.friendship_id as number));
    }
    if (rel.is_blocked_by_me) {
      return run(item.id, () => friendsApi.unblock(item.id));
    }
    if (!rel.is_friend && !rel.is_declined && !rel.is_blocked_me) {
      return run(item.id, () => friendsApi.send({ user_id: item.id }));
    }
  };

  const counts: Record<Tab, number> = {
    friends: friends.length,
    incoming: incoming.length,
    outgoing: outgoing.length,
    blocks: blocks.length,
  };

  return (
    <View style={styles.container}>
      <Text style={styles.screenTitle}>Друзья</Text>

      {/* ПОИСК */}
      <View style={styles.searchRow}>
        <TextInput
          style={styles.searchInput}
          value={query}
          onChangeText={setQuery}
          placeholder="Поиск по username или имени"
          placeholderTextColor="#666"
          onSubmitEditing={handleSearch}
          returnKeyType="search"
        />
        <Pressable style={styles.searchBtn} onPress={handleSearch} disabled={searching}>
          {searching ? (
            <ActivityIndicator color="#fff" size="small" />
          ) : (
            <Text style={styles.searchBtnText}>Найти</Text>
          )}
        </Pressable>
      </View>

      {error && <Text style={styles.error}>{error}</Text>}

      {/* РЕЗУЛЬТАТЫ ПОИСКА */}
      {searchResults && (
        <View style={styles.card}>
          <View style={styles.cardHeaderRow}>
            <Text style={styles.cardTitle}>
              Результаты поиска ({searchResults.length})
            </Text>
            <Pressable onPress={() => setSearchResults(null)}>
              <Text style={styles.closeLink}>Закрыть</Text>
            </Pressable>
          </View>

          {searchResults.length === 0 ? (
            <Text style={styles.empty}>Никого не нашли</Text>
          ) : (
            searchResults.map((item) => {
              const action = getSearchAction(item.relation);
              const disabled = action.kind === 'muted' || pendingId === item.id;
              return (
                <View key={item.id} style={styles.row}>
                  <Avatar user={item} />
                  <View style={styles.rowInfo}>
                    <Text style={styles.rowName}>
                      {item.first_name} {item.last_name || ''}
                    </Text>
                    <Text style={styles.rowUsername}>@{item.username}</Text>
                    {item.city ? <Text style={styles.rowMeta}>{item.city}</Text> : null}
                  </View>
                  <Pressable
                    style={[
                      styles.smallBtn,
                      action.kind === 'primary' && styles.smallBtnPrimary,
                      action.kind === 'ghost' && styles.smallBtnGhost,
                      disabled && styles.smallBtnDisabled,
                    ]}
                    disabled={disabled}
                    onPress={() => handleSearchAction(item)}
                  >
                    {pendingId === item.id ? (
                      <ActivityIndicator color="#fff" size="small" />
                    ) : (
                      <Text
                        style={[
                          styles.smallBtnText,
                          action.kind === 'ghost' && { color: '#bbb' },
                          disabled && { color: '#777' },
                        ]}
                      >
                        {action.label}
                      </Text>
                    )}
                  </Pressable>
                </View>
              );
            })
          )}
        </View>
      )}

      {/* ВКЛАДКИ */}
      <View style={styles.tabs}>
        {TABS.map((t) => (
          <Pressable
            key={t.key}
            style={[styles.tab, tab === t.key && styles.tabActive]}
            onPress={() => setTab(t.key)}
          >
            <Text style={[styles.tabText, tab === t.key && styles.tabTextActive]}>
              {t.label}
              {counts[t.key] > 0 ? ` (${counts[t.key]})` : ''}
            </Text>
          </Pressable>
        ))}
      </View>

      {/* СОДЕРЖИМОЕ ВКЛАДКИ */}
      <View style={styles.card}>
        {loading ? (
          <ActivityIndicator color="#c1121f" style={{ marginVertical: 24 }} />
        ) : (
          <>
            {tab === 'friends' &&
              (friends.length === 0 ? (
                <Text style={styles.empty}>
                  Пока нет друзей. Найдите пользователей через поиск выше.
                </Text>
              ) : (
                friends.map((f) => (
                  <View key={f.id} style={styles.row}>
                    <Avatar user={f.other_user as UserShort} />
                    <View style={styles.rowInfo}>
                      <Text style={styles.rowName}>
                        {f.other_user?.first_name} {f.other_user?.last_name || ''}
                      </Text>
                      <Text style={styles.rowUsername}>@{f.other_user?.username}</Text>
                    </View>
                    <Pressable
                      style={[styles.smallBtn, styles.smallBtnGhost]}
                      disabled={pendingId === f.id}
                      onPress={() =>
                        run(f.id, () => friendsApi.block({ user_id: f.other_user?.id as number }))
                      }
                    >
                      <Text style={[styles.smallBtnText, { color: '#bbb' }]}>Заблокировать</Text>
                    </Pressable>
                    <Pressable
                      style={[styles.smallBtn, styles.smallBtnDanger]}
                      disabled={pendingId === f.id}
                      onPress={() =>
                        run(f.id, () => friendsApi.remove(f.other_user?.id as number))
                      }
                    >
                      <Text style={styles.smallBtnText}>Удалить</Text>
                    </Pressable>
                  </View>
                ))
              ))}

            {tab === 'incoming' &&
              (incoming.length === 0 ? (
                <Text style={styles.empty}>Нет входящих заявок</Text>
              ) : (
                incoming.map((r) => (
                  <View key={r.id} style={styles.row}>
                    <Avatar user={r.other_user as UserShort} />
                    <View style={styles.rowInfo}>
                      <Text style={styles.rowName}>
                        {r.other_user?.first_name} {r.other_user?.last_name || ''}
                      </Text>
                      <Text style={styles.rowUsername}>@{r.other_user?.username}</Text>
                    </View>
                    <Pressable
                      style={[styles.smallBtn, styles.smallBtnPrimary]}
                      disabled={pendingId === r.id}
                      onPress={() => run(r.id, () => friendsApi.accept(r.id))}
                    >
                      <Text style={styles.smallBtnText}>Принять</Text>
                    </Pressable>
                    <Pressable
                      style={[styles.smallBtn, styles.smallBtnDanger]}
                      disabled={pendingId === r.id}
                      onPress={() => run(r.id, () => friendsApi.decline(r.id))}
                    >
                      <Text style={styles.smallBtnText}>Отклонить</Text>
                    </Pressable>
                  </View>
                ))
              ))}

            {tab === 'outgoing' &&
              (outgoing.length === 0 ? (
                <Text style={styles.empty}>Нет исходящих заявок</Text>
              ) : (
                outgoing.map((r) => (
                  <View key={r.id} style={styles.row}>
                    <Avatar user={r.other_user as UserShort} />
                    <View style={styles.rowInfo}>
                      <Text style={styles.rowName}>
                        {r.other_user?.first_name} {r.other_user?.last_name || ''}
                      </Text>
                      <Text style={styles.rowUsername}>@{r.other_user?.username}</Text>
                      <Text style={styles.rowMeta}>Ожидает ответа</Text>
                    </View>
                    <Pressable
                      style={[styles.smallBtn, styles.smallBtnGhost]}
                      disabled={pendingId === r.id}
                      onPress={() => run(r.id, () => friendsApi.cancel(r.id))}
                    >
                      <Text style={[styles.smallBtnText, { color: '#bbb' }]}>Отменить</Text>
                    </Pressable>
                  </View>
                ))
              ))}

            {tab === 'blocks' &&
              (blocks.length === 0 ? (
                <Text style={styles.empty}>Чёрный список пуст</Text>
              ) : (
                blocks.map((b) => (
                  <View key={b.id} style={styles.row}>
                    <Avatar user={b.blocked} />
                    <View style={styles.rowInfo}>
                      <Text style={styles.rowName}>
                        {b.blocked.first_name} {b.blocked.last_name || ''}
                      </Text>
                      <Text style={styles.rowUsername}>@{b.blocked.username}</Text>
                    </View>
                    <Pressable
                      style={[styles.smallBtn, styles.smallBtnGhost]}
                      disabled={pendingId === b.id}
                      onPress={() => run(b.id, () => friendsApi.unblock(b.blocked_id))}
                    >
                      <Text style={[styles.smallBtnText, { color: '#bbb' }]}>Разблокировать</Text>
                    </Pressable>
                  </View>
                ))
              ))}
          </>
        )}
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { paddingBottom: 40 },
  screenTitle: { color: '#fdf0d5', fontSize: 24, fontWeight: 'bold', marginBottom: 16 },

  searchRow: { flexDirection: 'row', gap: 10, marginBottom: 12 },
  searchInput: {
    flex: 1,
    backgroundColor: '#1a1a1a',
    borderWidth: 1,
    borderColor: '#333',
    borderRadius: 12,
    paddingHorizontal: 14,
    paddingVertical: 10,
    color: '#fdf0d5',
    fontSize: 15,
  },
  searchBtn: {
    backgroundColor: '#c1121f',
    borderRadius: 12,
    paddingHorizontal: 20,
    justifyContent: 'center',
    alignItems: 'center',
    minWidth: 90,
  },
  searchBtnText: { color: '#fff', fontWeight: '800', fontSize: 14 },

  error: { color: '#ff8a8a', marginBottom: 10, fontSize: 14 },

  tabs: { flexDirection: 'row', flexWrap: 'wrap', gap: 8, marginBottom: 12 },
  tab: {
    backgroundColor: '#1a1a1a',
    borderWidth: 1,
    borderColor: '#333',
    borderRadius: 20,
    paddingHorizontal: 14,
    paddingVertical: 8,
  },
  tabActive: { backgroundColor: 'rgba(193,18,31,0.25)', borderColor: '#c1121f' },
  tabText: { color: '#999', fontSize: 13, fontWeight: '600' },
  tabTextActive: { color: '#fdf0d5' },

  card: {
    backgroundColor: '#1a1a1a',
    borderRadius: 16,
    borderWidth: 1,
    borderColor: '#333',
    padding: 16,
    marginBottom: 12,
  },
  cardHeaderRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  cardTitle: { color: '#fdf0d5', fontSize: 16, fontWeight: '800' },
  closeLink: { color: '#888', fontSize: 13 },

  row: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
    paddingVertical: 10,
    borderBottomWidth: 1,
    borderBottomColor: '#2a2a2a',
    flexWrap: 'wrap',
  },
  avatar: { borderRadius: 24, backgroundColor: '#2a2a2a' },
  avatarPlaceholder: {
    borderRadius: 24,
    backgroundColor: '#2a2a2a',
    justifyContent: 'center',
    alignItems: 'center',
  },
  avatarEmoji: { color: '#c1121f', fontWeight: '800' },
  rowInfo: { flex: 1, minWidth: 140 },
  rowName: { color: '#fdf0d5', fontSize: 15, fontWeight: '700' },
  rowUsername: { color: '#888', fontSize: 13, marginTop: 2 },
  rowMeta: { color: '#666', fontSize: 12, marginTop: 2 },

  smallBtn: {
    borderRadius: 10,
    paddingHorizontal: 12,
    paddingVertical: 8,
    backgroundColor: '#333',
    alignItems: 'center',
  },
  smallBtnPrimary: { backgroundColor: '#c1121f' },
  smallBtnGhost: { backgroundColor: 'transparent', borderWidth: 1, borderColor: '#444' },
  smallBtnDanger: { backgroundColor: 'transparent', borderWidth: 1, borderColor: '#7a2230' },
  smallBtnDisabled: { opacity: 0.6 },
  smallBtnText: { color: '#fff', fontSize: 13, fontWeight: '700' },

  empty: { color: '#888', fontSize: 14, textAlign: 'center', paddingVertical: 20 },
});
