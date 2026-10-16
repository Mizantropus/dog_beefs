// Определения действий + какие параметры нужны каждому поддействию.
import { api } from './api'

// Подгружает /api/catalog/actions и строит карту key -> определение.
export async function loadActions() {
  const list = await api('/catalog/actions')
  const byKey = {}
  for (const a of list) byKey[a.key] = a
  return byKey
}

// Параметры для каждого поддействия (option).
const OPTION_PARAMS = {
  take_resource: ['district_id', 'resource', 'target_seat'],
  place_resource: ['district_id', 'resource', 'amount', 'target_seat'],
  lift_kompromat: ['district_id'],
  mine: ['district_id'],
  demine: ['district_id'],
  add_mangy: ['district_id'],
  recruit_mangy: ['district_id'],
  build: ['district_id'],
  destroy_building: ['district_id'],
  destroy_bridge: ['district_id', 'to_district'],
  repair_bridge: ['district_id', 'to_district']
}

// Какие параметры нужны для действия (standard_key + option).
export function paramsFor(standardKey, option) {
  if (standardKey === 'move') return ['district_id', 'to_district', 'dogs_count', 'mangy_count']
  if (standardKey === 'start_fight') return ['district_id', 'defender']
  return OPTION_PARAMS[option] || []
}

export const PARAM_LABELS = {
  district_id: 'Район',
  to_district: 'Куда (район)',
  resource: 'Ресурс',
  amount: 'Сумма',
  target_seat: 'На кого',
  defender: 'Соперник',
  active: 'Активная (заминировать)',
  dogs_count: 'Псов',
  mangy_count: 'Шелудивых'
}

export const RESOURCES = [
  { value: 'money', text: 'Деньги' },
  { value: 'kompromat', text: 'Компромат' },
  { value: 'explosive', text: 'Взрывчатка' }
]