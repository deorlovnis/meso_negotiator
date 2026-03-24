import { ArrowRightLeft, Lock, X } from 'lucide-react'
import type { SecuredOffer } from '../types'

interface CompareOffersModalProps {
  securedOffers: SecuredOffer[]
  onAgree: (index: number) => void
  onClose: () => void
}

export function CompareOffersModal({ securedOffers, onAgree, onClose }: CompareOffersModalProps) {
  return (
    <div className="fixed inset-0 z-[200] flex items-center justify-center p-4 sm:p-6">
      {/* biome-ignore lint/a11y/noStaticElementInteractions: modal backdrop dismiss */}
      <div
        role="presentation"
        className="absolute inset-0 bg-slate-900/40 backdrop-blur-sm"
        onClick={onClose}
        onKeyDown={(e) => e.key === 'Escape' && onClose()}
      />
      <div className="relative bg-white rounded-2xl shadow-2xl w-full max-w-5xl flex flex-col overflow-hidden border border-slate-200">
        {/* Header */}
        <div className="p-5 sm:p-6 border-b border-slate-100 flex items-center justify-between bg-white">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-full bg-slate-100 flex items-center justify-center">
              <ArrowRightLeft className="w-5 h-5 text-slate-600" />
            </div>
            <div>
              <h2 className="text-xl font-bold text-slate-900">Compare Offers</h2>
              <p className="text-xs text-slate-500 font-medium mt-0.5">
                Evaluate active round vs your fallbacks
              </p>
            </div>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="p-2 hover:bg-slate-100 rounded-full transition-colors text-slate-500"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Table */}
        <div className="p-0 overflow-auto max-h-[70vh]">
          <table className="w-full text-left border-collapse min-w-[800px]">
            <thead className="bg-[#f6f4f2]/80 sticky top-0 z-10 backdrop-blur-md">
              <tr>
                <th className="p-4 pl-6 text-[11px] font-bold text-slate-500 uppercase tracking-wider border-b border-slate-200">
                  Bot Rank
                </th>
                <th className="p-4 text-[11px] font-bold text-slate-500 uppercase tracking-wider border-b border-slate-200">
                  Offer Name
                </th>
                <th className="p-4 text-[11px] font-bold text-slate-500 uppercase tracking-wider border-b border-slate-200">
                  Price (per unit)
                </th>
                <th className="p-4 text-[11px] font-bold text-slate-500 uppercase tracking-wider border-b border-slate-200">
                  Delivery Time
                </th>
                <th className="p-4 text-[11px] font-bold text-slate-500 uppercase tracking-wider border-b border-slate-200">
                  Payment Terms
                </th>
                <th className="p-4 text-[11px] font-bold text-slate-500 uppercase tracking-wider border-b border-slate-200">
                  Contract Length
                </th>
                <th className="p-4 pr-6 border-b border-slate-200 w-36" />
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {securedOffers.map((offer, idx) => (
                <tr key={offer.rank} className="group hover:bg-slate-50 transition-colors">
                  <td className="p-4 pl-6">
                    <div className="flex items-center gap-2.5">
                      <span className="font-bold text-slate-400 text-sm">#{offer.rank}</span>
                      {idx === 0 && (
                        <span className="bg-[#10B981]/15 text-[#10B981] text-[10px] font-bold px-2.5 py-1 rounded-md whitespace-nowrap shadow-sm">
                          Fastest to deal
                        </span>
                      )}
                    </div>
                  </td>
                  <td className="p-4">
                    <div className="flex flex-col">
                      <span className="font-bold text-slate-900 text-sm">
                        {offer.label.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase())}
                      </span>
                      <span className="text-[10px] text-[#a59080] font-semibold flex items-center gap-1 mt-0.5">
                        <Lock className="w-2.5 h-2.5" /> Saved in Round {offer.round_secured}
                      </span>
                    </div>
                  </td>
                  <td className="p-4">
                    <span className="text-sm font-medium text-slate-700">{offer.terms.price}</span>
                  </td>
                  <td className="p-4">
                    <span className="text-sm font-medium text-slate-700">
                      {offer.terms.delivery}
                    </span>
                  </td>
                  <td className="p-4">
                    <span className="text-sm font-medium text-slate-700">
                      {offer.terms.payment}
                    </span>
                  </td>
                  <td className="p-4">
                    <span className="text-sm font-medium text-slate-700">
                      {offer.terms.contract}
                    </span>
                  </td>
                  <td className="p-4 pr-6 text-right w-[140px] align-middle">
                    <div className="flex flex-col items-end gap-1.5 opacity-0 group-hover:opacity-100 transition-all">
                      <button
                        type="button"
                        onClick={() => onAgree(idx)}
                        className="bg-[#4C6B56] text-white text-[11px] font-bold uppercase tracking-wider px-4 py-1.5 rounded-lg hover:bg-[#3a5242] shadow-sm hover:shadow-md transition-all w-full"
                      >
                        Agree
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Footer */}
        <div className="p-4 border-t border-slate-100 bg-slate-50 flex justify-center">
          <button
            type="button"
            onClick={onClose}
            className="text-xs font-bold text-slate-500 hover:text-slate-800 transition-colors uppercase tracking-wider py-2 px-6 border border-slate-200 rounded-lg hover:bg-white shadow-sm"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  )
}
