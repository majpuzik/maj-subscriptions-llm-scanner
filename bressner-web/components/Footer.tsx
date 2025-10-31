'use client';

import Link from 'next/link';
import { useLanguage } from '@/contexts/LanguageContext';

export default function Footer() {
  const { language } = useLanguage();

  return (
    <footer className="bg-[#1a1a1a] text-white">
      {/* Newsletter Section */}
      <div className="bg-[#00AEEF] py-8">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex flex-col md:flex-row items-center justify-between gap-6">
            <div>
              <h3 className="text-2xl font-bold text-white mb-2">
                {language === 'de' ? 'Newsletter abonnieren' : language === 'en' ? 'Subscribe to Newsletter' : 'Přihlásit se k newsletteru'}
              </h3>
              <p className="text-white/90">
                {language === 'de'
                  ? 'Bleiben Sie informiert über neue Produkte und Technologien'
                  : language === 'en'
                  ? 'Stay informed about new products and technologies'
                  : 'Zůstaňte informováni o nových produktech a technologiích'
                }
              </p>
            </div>
            <div className="flex gap-2 w-full md:w-auto">
              <input
                type="email"
                placeholder={language === 'de' ? 'Ihre E-Mail-Adresse' : language === 'en' ? 'Your email address' : 'Vaše e-mailová adresa'}
                className="flex-1 md:w-80 px-4 py-3 rounded-lg text-gray-900 focus:outline-none focus:ring-2 focus:ring-white"
              />
              <button className="bg-white text-[#00AEEF] px-6 py-3 rounded-lg font-bold hover:bg-gray-100 transition-colors whitespace-nowrap">
                {language === 'de' ? 'Abonnieren' : language === 'en' ? 'Subscribe' : 'Přihlásit'}
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Main Footer */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
          {/* Company Info */}
          <div>
            <h3 className="text-2xl font-bold mb-4">
              BRESSNER<span className="text-[#00AEEF]">.technology</span>
            </h3>
            <p className="text-gray-400 text-sm leading-relaxed mb-4">
              {language === 'de'
                ? 'Ihr Partner für industrielle Hardware-Lösungen und IoT-Systeme in der Tschechischen Republik.'
                : language === 'en'
                ? 'Your partner for industrial hardware solutions and IoT systems in the Czech Republic.'
                : 'Váš partner pro průmyslová hardware řešení a IoT systémy v České republice.'
              }
            </p>
            <div className="flex gap-3">
              <a href="https://www.linkedin.com/company/bressner-technology" target="_blank" rel="noopener noreferrer" className="w-10 h-10 bg-gray-700 hover:bg-[#00AEEF] rounded-full flex items-center justify-center transition-colors">
                <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M19 0h-14c-2.761 0-5 2.239-5 5v14c0 2.761 2.239 5 5 5h14c2.762 0 5-2.239 5-5v-14c0-2.761-2.238-5-5-5zm-11 19h-3v-11h3v11zm-1.5-12.268c-.966 0-1.75-.79-1.75-1.764s.784-1.764 1.75-1.764 1.75.79 1.75 1.764-.783 1.764-1.75 1.764zm13.5 12.268h-3v-5.604c0-3.368-4-3.113-4 0v5.604h-3v-11h3v1.765c1.396-2.586 7-2.777 7 2.476v6.759z"/>
                </svg>
              </a>
              <a href="https://twitter.com/bressner_tech" target="_blank" rel="noopener noreferrer" className="w-10 h-10 bg-gray-700 hover:bg-[#00AEEF] rounded-full flex items-center justify-center transition-colors">
                <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M23 3a10.9 10.9 0 01-3.14 1.53 4.48 4.48 0 00-7.86 3v1A10.66 10.66 0 013 4s-4 9 5 13a11.64 11.64 0 01-7 2c9 5 20 0 20-11.5a4.5 4.5 0 00-.08-.83A7.72 7.72 0 0023 3z"/>
                </svg>
              </a>
            </div>
          </div>

          {/* Kontakt */}
          <div>
            <h4 className="text-lg font-bold mb-4">Kontakt</h4>
            <ul className="space-y-3 text-sm text-gray-400">
              <li>
                <strong className="text-white">Bressner Technology s.r.o.</strong>
              </li>
              <li>Ocelkova 643/20</li>
              <li>198 00 Praha 9, Černý Most</li>
              <li>Česká republika</li>
              <li className="pt-2">
                <a href="tel:+420251109954" className="hover:text-[#00AEEF] transition-colors">
                  Tel: +420 251 109 954
                </a>
              </li>
              <li>
                <a href="mailto:kunst@bressner.cz" className="hover:text-[#00AEEF] transition-colors">
                  E-Mail: kunst@bressner.cz
                </a>
              </li>
            </ul>
          </div>

          {/* Support */}
          <div>
            <h4 className="text-lg font-bold mb-4">Support</h4>
            <ul className="space-y-2 text-sm">
              <li>
                <a href="/support" className="text-gray-400 hover:text-[#00AEEF] transition-colors">
                  {language === 'de' ? 'Technischer Support' : language === 'en' ? 'Technical Support' : 'Technická podpora'}
                </a>
              </li>
              <li>
                <a href="/downloads" className="text-gray-400 hover:text-[#00AEEF] transition-colors">
                  Download Portal
                </a>
              </li>
              <li>
                <a href="/dokumentation" className="text-gray-400 hover:text-[#00AEEF] transition-colors">
                  {language === 'de' ? 'Dokumentation' : language === 'en' ? 'Documentation' : 'Dokumentace'}
                </a>
              </li>
              <li>
                <a href="/faq" className="text-gray-400 hover:text-[#00AEEF] transition-colors">
                  FAQ
                </a>
              </li>
              <li>
                <a href="/rma" className="text-gray-400 hover:text-[#00AEEF] transition-colors">
                  RMA / {language === 'de' ? 'Rücksendung' : language === 'en' ? 'Returns' : 'Vrácení'}
                </a>
              </li>
            </ul>
          </div>

          {/* Rechtliches */}
          <div>
            <h4 className="text-lg font-bold mb-4">
              {language === 'de' ? 'Rechtliches' : language === 'en' ? 'Legal' : 'Právní informace'}
            </h4>
            <ul className="space-y-2 text-sm">
              <li>
                <Link href="/impressum" className="text-gray-400 hover:text-[#00AEEF] transition-colors">
                  Impressum
                </Link>
              </li>
              <li>
                <Link href="/datenschutz" className="text-gray-400 hover:text-[#00AEEF] transition-colors">
                  Datenschutzerklärung
                </Link>
              </li>
              <li>
                <Link href="/cookies" className="text-gray-400 hover:text-[#00AEEF] transition-colors">
                  Cookie-Richtlinie (EU)
                </Link>
              </li>
              <li>
                <Link href="/agb" className="text-gray-400 hover:text-[#00AEEF] transition-colors">
                  AGB
                </Link>
              </li>
              <li>
                <Link href="/widerruf" className="text-gray-400 hover:text-[#00AEEF] transition-colors">
                  {language === 'de' ? 'Widerrufsrecht' : language === 'en' ? 'Right of Withdrawal' : 'Právo na odstoupení'}
                </Link>
              </li>
            </ul>
          </div>
        </div>

        {/* Bottom Bar */}
        <div className="border-t border-gray-800 mt-12 pt-8">
          <div className="flex flex-col md:flex-row justify-between items-center gap-4 text-sm text-gray-400">
            <p>
              © {new Date().getFullYear()} Bressner Technology s.r.o. {language === 'de' ? 'Alle Rechte vorbehalten' : language === 'en' ? 'All rights reserved' : 'Všechna práva vyhrazena'}.
            </p>
            <div className="flex gap-6">
              <span>IČO: 27566021</span>
              <span>DIČ: CZ27566021</span>
              <span>
                {language === 'de' ? 'Geschäftsführerin' : language === 'en' ? 'Managing Director' : 'Jednatelka'}: Ing. Zuzana Pužíková
              </span>
            </div>
          </div>
          <div className="text-center text-xs text-gray-500 mt-4">
            C 113048 vedená u Městského soudu v Praze
          </div>
        </div>
      </div>
    </footer>
  );
}
