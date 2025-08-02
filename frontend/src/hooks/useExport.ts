import { useCallback } from 'react';
import { useAppStore } from '../store/useAppStore';
import { ExportOptions } from '../types';
import Papa from 'papaparse';
import jsPDF from 'jspdf';

export const useExport = () => {
  const { routes, routingSummary } = useAppStore();
  const currentRoutes = routes;

  const exportRoutes = useCallback(async (options: ExportOptions) => {
    if (!currentRoutes.length) {
      throw new Error('No routes to export');
    }

    if (options.format === 'csv') {
      await exportAsCSV(options);
    } else if (options.format === 'pdf') {
      await exportAsPDF(options);
    }
  }, [currentRoutes, routingSummary]);

  const exportAsCSV = useCallback(async (options: ExportOptions) => {
    const csvData: any[] = [];

    // Route summary data
    csvData.push(['Route Summary']);
    csvData.push(['Truck ID', 'Stops Count', 'Total Miles', 'Total Hours', 'Fuel Cost', 'Utilization %']);
    
    currentRoutes.forEach(route => {
      csvData.push([
        route.truck_id,
        route.stops.length,
        route.total_miles.toFixed(1),
        route.total_time_hours.toFixed(1),
        route.fuel_estimate.toFixed(2),
        route.utilization_percent
      ]);
    });

    csvData.push([]); // Empty row

    // Detailed stops data
    csvData.push(['Detailed Stops']);
    csvData.push(['Truck ID', 'Stop ID', 'Stop Order', 'ETA', 'Distance from Previous', 'Notes']);

    currentRoutes.forEach(route => {
      route.stops.forEach((stop, index) => {
        csvData.push([
          route.truck_id,
          stop.stop_id,
          index + 1,
          stop.eta,
          stop.distance_from_previous.toFixed(1),
          stop.notes || ''
        ]);
      });
    });

    if (options.includeSummary && routingSummary) {
      csvData.push([]); // Empty row
      csvData.push(['AI Analysis']);
      csvData.push(['Summary']);
      
      // Split summary into manageable chunks for CSV
      const summaryLines = routingSummary.split('\n');
      summaryLines.forEach((line: string) => {
        if (line.trim()) {
          csvData.push([line.trim()]);
        }
      });
    }

    // Convert to CSV and download
    const csv = Papa.unparse(csvData);
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    const url = URL.createObjectURL(blob);
    
    link.setAttribute('href', url);
    link.setAttribute('download', `routes_${new Date().toISOString().split('T')[0]}.csv`);
    link.style.visibility = 'hidden';
    
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  }, [currentRoutes, routingSummary]);

  const exportAsPDF = useCallback(async (options: ExportOptions) => {
    const pdf = new jsPDF();
    let yPosition = 20;
    const pageWidth = pdf.internal.pageSize.width;
    const margin = 20;
    const lineHeight = 6;

    // Helper function to add text with word wrapping
    const addText = (text: string, x: number, y: number, maxWidth?: number) => {
      if (maxWidth) {
        const lines = pdf.splitTextToSize(text, maxWidth);
        pdf.text(lines, x, y);
        return y + (lines.length * lineHeight);
      } else {
        pdf.text(text, x, y);
        return y + lineHeight;
      }
    };

    // Helper function to check if we need a new page
    const checkNewPage = (requiredSpace: number) => {
      if (yPosition + requiredSpace > pdf.internal.pageSize.height - margin) {
        pdf.addPage();
        yPosition = 20;
      }
    };

    // Title
    pdf.setFontSize(20);
    pdf.setFont('helvetica', 'bold');
    yPosition = addText('FlowLogic RouteAI - Route Analysis', margin, yPosition);
    
    pdf.setFontSize(10);
    pdf.setFont('helvetica', 'normal');
    yPosition = addText(`Generated: ${new Date().toLocaleString()}`, margin, yPosition + 5);
    yPosition += 10;

    // Executive Summary
    pdf.setFontSize(14);
    pdf.setFont('helvetica', 'bold');
    checkNewPage(30);
    yPosition = addText('Executive Summary', margin, yPosition);
    yPosition += 5;

    pdf.setFontSize(10);
    pdf.setFont('helvetica', 'normal');
    
    const totalStops = currentRoutes.reduce((sum, route) => sum + route.stops.length, 0);
    const totalMiles = currentRoutes.reduce((sum, route) => sum + route.total_miles, 0);
    const totalCost = currentRoutes.reduce((sum, route) => sum + route.fuel_estimate, 0);
    const avgUtilization = currentRoutes.reduce((sum, route) => sum + route.utilization_percent, 0) / currentRoutes.length;

    const summaryText = [
      `Total Routes: ${currentRoutes.length}`,
      `Total Stops: ${totalStops}`,
      `Total Distance: ${totalMiles.toFixed(1)} miles`,
      `Total Fuel Cost: $${totalCost.toFixed(2)}`,
      `Average Utilization: ${avgUtilization.toFixed(1)}%`,
      `Cost per Stop: $${(totalCost / totalStops).toFixed(2)}`
    ];

    summaryText.forEach(line => {
      checkNewPage(lineHeight);
      yPosition = addText(line, margin, yPosition);
    });
    yPosition += 10;

    // Route Details
    pdf.setFontSize(14);
    pdf.setFont('helvetica', 'bold');
    checkNewPage(30);
    yPosition = addText('Route Details', margin, yPosition);
    yPosition += 5;

    currentRoutes.forEach((route, index) => {
      checkNewPage(40);
      
      pdf.setFontSize(12);
      pdf.setFont('helvetica', 'bold');
      yPosition = addText(`Truck ${route.truck_id}`, margin, yPosition);
      
      pdf.setFontSize(10);
      pdf.setFont('helvetica', 'normal');
      yPosition = addText(`${route.stops.length} stops • ${route.total_miles.toFixed(1)} mi • ${route.total_time_hours.toFixed(1)}h • $${route.fuel_estimate.toFixed(2)} • ${route.utilization_percent}% utilization`, margin, yPosition);
      yPosition += 3;

      // Stops table
      route.stops.forEach((stop, stopIndex) => {
        checkNewPage(lineHeight);
        const stopText = `${stopIndex + 1}. Stop #${stop.stop_id} - ETA: ${stop.eta} (${stop.distance_from_previous.toFixed(1)} mi)`;
        yPosition = addText(stopText, margin + 10, yPosition);
        
        if (stop.notes) {
          checkNewPage(lineHeight);
          yPosition = addText(`   Notes: ${stop.notes}`, margin + 10, yPosition);
        }
      });

      if (route.reasoning) {
        checkNewPage(lineHeight * 2);
        yPosition = addText('Routing Logic:', margin + 10, yPosition);
        yPosition = addText(route.reasoning, margin + 10, yPosition, pageWidth - 2 * margin - 10);
      }
      
      yPosition += 10;
    });

    // AI Analysis
    if (options.includeSummary && routingSummary) {
      checkNewPage(40);
      
      pdf.setFontSize(14);
      pdf.setFont('helvetica', 'bold');
      yPosition = addText('AI Analysis & Recommendations', margin, yPosition);
      yPosition += 5;

      pdf.setFontSize(9);
      pdf.setFont('helvetica', 'normal');
      
      const summaryLines = routingSummary.split('\n');
      summaryLines.forEach((line: string) => {
        if (line.trim()) {
          checkNewPage(lineHeight);
          yPosition = addText(line.trim(), margin, yPosition, pageWidth - 2 * margin);
        }
      });
    }

    // Map placeholder
    if (options.includeMap) {
      checkNewPage(60);
      
      pdf.setFontSize(14);
      pdf.setFont('helvetica', 'bold');
      yPosition = addText('Route Map', margin, yPosition);
      yPosition += 10;

      // Draw a simple map placeholder
      pdf.setDrawColor(200, 200, 200);
      pdf.setFillColor(245, 245, 245);
      pdf.rect(margin, yPosition, pageWidth - 2 * margin, 80, 'FD');
      
      pdf.setFontSize(10);
      pdf.setTextColor(100, 100, 100);
      pdf.text('Route map visualization would appear here', pageWidth / 2, yPosition + 40, { align: 'center' });
      pdf.text('(Integrate with Mapbox GL JS for production)', pageWidth / 2, yPosition + 50, { align: 'center' });
      
      yPosition += 90;
    }

    // Save the PDF
    pdf.save(`routes_${new Date().toISOString().split('T')[0]}.pdf`);
  }, [currentRoutes, routingSummary]);

  return {
    exportRoutes,
  };
};